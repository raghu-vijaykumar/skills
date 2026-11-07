import React from "react";
import {Composition,registerRoot} from "remotion";
import {LikeShareSubscribe} from "./LikeShareSubscribe";

const Root:React.FC=()=> <Composition id="LikeShareSubscribe" component={LikeShareSubscribe}
  durationInFrames={120} fps={30} width={1920} height={1080}
  defaultProps={{accent:"#5b7cfa",subscribeColor:"#ed333b",textColor:"#ffffff",scale:1,bottom:90,labels:["LIKE","SHARE","SUBSCRIBE"]}}/>;
registerRoot(Root);
