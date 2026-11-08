// The source catalog is shipped with the skill; credentials belong to the channel workspace.
import fs from 'node:fs';
import path from 'node:path';
import {parseEnv} from 'node:util';
import {fileURLToPath} from 'node:url';
import {parse} from 'yaml';

const DEFAULT_SOURCES = fileURLToPath(new URL('../sources.yaml', import.meta.url));
const DEFAULT_SETTINGS = {title: 'Video Idea Digest', timezone: 'Asia/Kolkata', lookbackDays: 1, limitPerSection: 0};

export function loadSources(file = DEFAULT_SOURCES) {
  const parsed = parse(fs.readFileSync(file, 'utf8')) ?? {};
  const settings = {...DEFAULT_SETTINGS, ...(parsed.settings ?? {})};
  const topics = (parsed.topics ?? []).map((topic) => ({
    id: topic.id,
    label: topic.label ?? topic.id,
    emoji: topic.emoji ?? '',
    sources: (topic.sources ?? []).filter((source) => source.enabled !== false)
      .map((source) => ({...source, topic: topic.id})),
  }));
  const paperConfig = parsed.papers ?? {};
  const papers = {
    enabled: paperConfig.enabled !== false,
    limit: paperConfig.limit ?? settings.limitPerSection,
    minUpvotes: paperConfig.providers?.huggingface?.minUpvotes ?? 0,
    minPoints: paperConfig.providers?.hackernews?.minPoints ?? 0,
    huggingface: paperConfig.providers?.huggingface?.enabled !== false,
    hackernews: paperConfig.providers?.hackernews?.enabled !== false,
  };
  return {settings, topics, papers};
}

export function loadSecrets(workspace) {
  const envFile = path.join(workspace, 'code', 'secrets', 'digest.env');
  const env = fs.existsSync(envFile) ? parseEnv(fs.readFileSync(envFile, 'utf8')) : {};
  const jsonFile = path.join(workspace, 'code', 'secrets', 'digest.json');
  const file = fs.existsSync(jsonFile) ? JSON.parse(fs.readFileSync(jsonFile, 'utf8')) : {};
  return {
    telegramBotToken: process.env.TELEGRAM_BOT_TOKEN ?? env.TELEGRAM_BOT_TOKEN ?? file.telegram?.botToken ?? file.telegramBotToken,
    telegramChatId: process.env.TELEGRAM_CHAT_ID ?? env.TELEGRAM_CHAT_ID ?? file.telegram?.chatId ?? file.telegramChatId,
    githubToken: process.env.GITHUB_TOKEN ?? env.GITHUB_TOKEN ?? file.github?.token ?? file.githubToken,
  };
}

export function requireTelegram(secrets) {
  if (!secrets.telegramBotToken || !secrets.telegramChatId) {
    throw new Error('Telegram delivery requires TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in the environment or ignored code/secrets/digest.env');
  }
}
