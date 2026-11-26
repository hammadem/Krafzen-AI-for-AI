import model from "./cad_symbol_model.json";
export function classifyCadSymbol(pixels:number[]){
 if(pixels.length!==576||pixels.some(v=>!Number.isFinite(v)||v<0||v>1))throw Error("Invalid 24×24 normalized crop");
 const ink=pixels.reduce((a,b)=>a+b,0)/pixels.length;
 if(ink<0.025||ink>0.60)return {label:"unknown",confidence:0};
 const features:number[]=[];
 for(let y=0;y<8;y++)for(let x=0;x<8;x++){let n=0;for(let j=0;j<3;j++)for(let i=0;i<3;i++)n+=pixels[(y*3+j)*24+x*3+i];features.push(n/9);}
 const scores=model.weights.map((w,k)=>model.bias[k]+w.reduce((a,b,j)=>a+b*features[j],0));
 const max=Math.max(...scores),p=scores.map(v=>Math.exp(v-max)),sum=p.reduce((a,b)=>a+b,0),i=scores.indexOf(max),confidence=p[i]/sum;
 return {label:confidence>=model.confidence_threshold?model.labels[i]:"unknown",confidence};
}
