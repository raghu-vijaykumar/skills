import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import os from 'node:os';
import {spawnSync} from 'node:child_process';
import {test} from 'node:test';
import React from 'react';
import {renderToStaticMarkup} from 'react-dom/server';
import {approvePackage, sha256, verifyPackage, validateSrt, validateChecklist} from '../scripts/package.mjs';
import {transcriptionSegments, toSrt, transcribeDraft} from '../scripts/transcribe.mjs';
import {sourceRevision} from '../scripts/source-revision.mjs';
import {HairlineStage, HairlineCacheFigure} from '../skills/content-studio-videogen/dist/hairline.js';

const root = path.join(os.tmpdir(), 'content-studio-tests');
fs.mkdirSync(root, {recursive:true});
function fixture(kind='edited') {
  const workspace=fs.mkdtempSync(path.join(root,'content-studio-test-'));
  const channel=path.join(workspace,'sample');
  const draft=path.join(channel,'drafts','001-test');
  fs.mkdirSync(draft,{recursive:true});
  fs.writeFileSync(path.join(draft,'video.mp4'),'test master bytes');
  fs.writeFileSync(path.join(draft,'title.txt'),'Exact title\n');
  fs.writeFileSync(path.join(draft,'description.txt'),'Exact description\n');
  fs.writeFileSync(path.join(draft,'thumbnail.png'),'thumbnail');
  fs.writeFileSync(path.join(draft,'creative.json'),JSON.stringify({themeId:'neutral',styleId:'hairline',format:'long',renderer:kind==='remotion'?'remotion':'manual',choices:['mechanism hook']}));
  fs.writeFileSync(path.join(draft,'draft.json'),JSON.stringify({production:{kind}}));
  if(kind==='edited') {
    fs.writeFileSync(path.join(draft,'transcript.json'),JSON.stringify({masterSha256:sha256(path.join(draft,'video.mp4')),segments:[{startMs:0,endMs:1000,text:'Hello'}]}));
    fs.writeFileSync(path.join(draft,'captions.srt'),'1\n00:00:00,000 --> 00:00:01,000\nHello\n');
  } else {
    fs.mkdirSync(path.join(draft,'content'));
    fs.writeFileSync(path.join(draft,'content','video.yaml'),'video:\n  compositionId: Test\n');
  }
  return {workspace,channel,draft};
}
function cleanup(workspace) {
  const resolved=path.resolve(workspace);
  if(!resolved.startsWith(root+path.sep) || fs.lstatSync(resolved).isSymbolicLink()) throw new Error('Unsafe test cleanup');
  fs.rmSync(resolved,{recursive:true,force:true});
}
function writeChecklist(draft, mutate = null) {
  const items=Array.from({length:17},(_,index)=>({
    id:`C${String(index+1).padStart(2,'0')}`,
    phase:'pre_publish',
    status:'done',
    evidence:['reviewed'],
    reason:'',
    note:'reviewed',
  }));
  if(mutate) mutate(items);
  fs.writeFileSync(path.join(draft,'lifecycle-checklist.json'),JSON.stringify({items}));
}

test('main lifecycle checklist blocks approval until every item is covered',()=>{
  const {workspace,draft}=fixture();
  try {
    writeChecklist(draft,(items)=>{items[0].status='pending';});
    assert.throws(()=>approvePackage(draft,'001-test','Reviewed'),/Lifecycle checklist incomplete: C01: pending/);
    writeChecklist(draft,(items)=>{items[0].status='not_applicable';items[0].reason='';});
    assert.throws(()=>approvePackage(draft,'001-test','Reviewed'),/C01: not_applicable without reason/);
    writeChecklist(draft);
    approvePackage(draft,'001-test','Reviewed with checklist');
    assert.equal(validateChecklist(draft,'pre_publish').items.length,17);
  } finally {cleanup(workspace);}
});

test('a main lifecycle draft cannot approve without its checklist',()=>{
  const {workspace,draft}=fixture();
  try {
    fs.writeFileSync(path.join(draft,'draft.json'),JSON.stringify({production:{kind:'edited'},lifecycle:'main'}));
    assert.throws(()=>approvePackage(draft,'001-test','Reviewed'),/requires lifecycle-checklist.json/);
  } finally {cleanup(workspace);}
});

test('one approval fingerprints edited inputs and rejects a changed master',()=>{
  const {workspace,draft}=fixture();
  try {
    assert.throws(()=>approvePackage(draft,'001-test',''),/Approval note/);
    approvePackage(draft,'001-test','Reviewed final export and thumbnail');
    assert.equal(verifyPackage(draft,'001-test').files.master,path.join(draft,'video.mp4'));
    fs.appendFileSync(path.join(draft,'video.mp4'),'changed');
    assert.throws(()=>verifyPackage(draft,'001-test'),/transcript\/captions do not match/);
  } finally {cleanup(workspace);}
});

test('creative record and edited captions are approval gates',()=>{
  const {workspace,draft}=fixture();
  try {
    fs.rmSync(path.join(draft,'creative.json'));
    assert.throws(()=>approvePackage(draft,'001-test','Reviewed'),/creative.json/);
    fs.writeFileSync(path.join(draft,'creative.json'),JSON.stringify({themeId:'neutral',styleId:'manual',format:'long',renderer:'manual',choices:[]}));
    fs.rmSync(path.join(draft,'captions.srt'));
    assert.throws(()=>approvePackage(draft,'001-test','Reviewed'),/captions.srt/);
  } finally {cleanup(workspace);}
});

test('Remotion package uses the same approval gate and shared dry-run publisher',()=>{
  const {workspace,channel,draft}=fixture('remotion');
  try {
    const config=path.join(workspace,'channels.json');
    fs.writeFileSync(config,'\uFEFF'+JSON.stringify({workspace,channels:{sample:{name:'Sample'}}}));
    const cli=path.resolve('content-studio/scripts/cli.mjs');
    const invoke=(...args)=>spawnSync(process.execPath,[cli,'publish','--channel','sample','--draft','001-test','--config',config,...args],{encoding:'utf8'});
    const now=invoke();
    assert.equal(now.status,0,now.stderr);
    assert.equal(JSON.parse(now.stdout).dryRun,true);
    const future=invoke('--at','2030-12-01T18:00:00+05:30');
    assert.equal(future.status,0,future.stderr);
    assert.equal(JSON.parse(future.stdout).publishAt,'2030-12-01T12:30:00.000Z');
    const instagram=invoke('--platform','instagram');
    assert.equal(instagram.status,0,instagram.stderr);
    assert.equal(JSON.parse(instagram.stdout).platform,'instagram');
    assert.notEqual(invoke('--platform','instagram','--at','2030-12-01T18:00:00+05:30').status,0);
    assert.match(invoke('--confirm').stderr,/approval is missing/);
    approvePackage(draft,'001-test','Reviewed Remotion master and package');
    assert.match(sourceRevision(channel,draft),/^approved:[a-f0-9]{64}$/);
  } finally {cleanup(workspace);}
});

test('caption gate rejects overlaps and timestamps beyond the export',()=>{
  const {workspace,draft}=fixture();
  try {
    const captions=path.join(draft,'captions.srt');
    fs.writeFileSync(captions,'1\n00:00:00,000 --> 00:00:02,000\nOne\n\n2\n00:00:01,000 --> 00:00:03,000\nTwo\n');
    assert.throws(()=>validateSrt(captions,5),/invalid timing/);
    fs.writeFileSync(captions,'1\n00:00:04,000 --> 00:00:06,000\nToo late\n');
    assert.throws(()=>validateSrt(captions,5),/invalid timing/);
  } finally {cleanup(workspace);}
});

test('whisper JSON segments produce timed captions',()=>{
  const segments=transcriptionSegments({transcription:[{offsets:{from:250,to:1250},text:'  Hello world  '}]});
  assert.deepEqual(segments,[{startMs:250,endMs:1250,text:'Hello world'}]);
  assert.match(toSrt(segments),/00:00:00,250 --> 00:00:01,250/);
});

test('edited-export transcription writes caption and representative-frame references',()=>{
  const {workspace,channel,draft}=fixture();
  try {
    const cli=path.join(workspace,'whisper-cli.exe');
    const model=path.join(workspace,'ggml-small.bin');
    fs.writeFileSync(cli,'stub');
    fs.writeFileSync(model,'stub');
    const commands=[];
    const result=transcribeDraft(channel,draft,{cli,model,
      probe:()=>({durationSeconds:10}),
      runCommand:(binary,args,label)=>{
        commands.push({binary,args,label});
        if(label==='whisper.cpp transcription') {
          const prefix=args[args.indexOf('-of')+1];
          fs.writeFileSync(`${prefix}.json`,JSON.stringify({transcription:[
            {offsets:{from:100,end:1000,to:1000},text:'A real sentence'}]}));
        } else {
          fs.writeFileSync(args[args.length-1],'proof');
        }
      }});
    assert.equal(result.segments,1);
    assert.match(fs.readFileSync(result.captions,'utf8'),/A real sentence/);
    assert.equal(commands.filter((entry)=>entry.label==='reference frame').length,3);
    assert.ok(commands.find((entry)=>entry.label==='whisper.cpp transcription').args.includes('auto'));
  } finally {cleanup(workspace);}
});

test('Hairline stage is deterministic per frame and changes across a motion range',()=>{
  const theme={colors:{text:'#ffffff',accent:'#00bbaa',background:'#09141c'}};
  const draw=(frame)=>renderToStaticMarkup(React.createElement(HairlineStage,{frame,fps:30,durationInFrames:30,theme,figure:HairlineCacheFigure}));
  assert.equal(draw(15),draw(15));
  assert.notEqual(draw(0),draw(15));
  assert.notEqual(draw(15),draw(29));
});
