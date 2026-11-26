// Reproduce the actual training run; no external dependencies or network.
import fs from "node:fs";
function train(){
 const labels=["column","door_swing","duct","pipe_circle","window","annotation_arrow"];
 const N=24,D=64;function rng(seed){let x=seed>>>0;return ()=>{x=(Math.imul(1664525,x)+1013904223)>>>0;return x/4294967296;};}
 const primitives={
 column:[[-.46,-.46,.46,-.46],[.46,-.46,.46,.46],[.46,.46,-.46,.46],[-.46,.46,-.46,-.46],[-.46,-.46,.46,.46],[-.46,.46,.46,-.46]],
 door_swing:[[-.52,.52,.52,.52],[-.52,.52,-.52,-.52],...Array.from({length:14},(_,i)=>{let a=i*Math.PI/28,b=(i+1)*Math.PI/28;return[-.52+1.04*Math.sin(a),.52-1.04*Math.cos(a),-.52+1.04*Math.sin(b),.52-1.04*Math.cos(b)];})],
 duct:[[-.68,-.27,.68,-.27],[.68,-.27,.68,.27],[.68,.27,-.68,.27],[-.68,.27,-.68,-.27],[-.68,0,.68,0]],
 pipe_circle:Array.from({length:32},(_,i)=>{let a=i*Math.PI/16,b=(i+1)*Math.PI/16;return[.47*Math.cos(a),.47*Math.sin(a),.47*Math.cos(b),.47*Math.sin(b)];}),
 window:[[-.65,-.19,.65,-.19],[-.65,.19,.65,.19],[-.65,-.19,-.65,.19],[.65,-.19,.65,.19],[0,-.19,0,.19]],
 annotation_arrow:[[-.65,0,.65,0],[.65,0,.23,-.28],[.65,0,.23,.28]]
 };
 function render(label,seed,test=false){let rand=rng(seed),angle=(rand()-.5)*(test?.70:.60),scale=.83+rand()*.20,dx=(rand()-.5)*.16,dy=(rand()-.5)*.16,stroke=.045+rand()*.035;let ca=Math.cos(angle),sa=Math.sin(angle);
 let segments=primitives[label].map(s=>{let t=(x,y)=>[scale*(ca*x-sa*y)+dx,scale*(sa*x+ca*y)+dy];return [...t(s[0],s[1]),...t(s[2],s[3])];});
 let out=[];for(let y=0;y<N;y++)for(let x=0;x<N;x++){let px=(x+.5)/N*2-1,py=(y+.5)/N*2-1;let ink=segments.some(([ax,ay,bx,by])=>{let vx=bx-ax,vy=by-ay,t=Math.max(0,Math.min(1,((px-ax)*vx+(py-ay)*vy)/(vx*vx+vy*vy||1)));return Math.hypot(px-ax-t*vx,py-ay-t*vy)<stroke;});out.push((rand()<(test?.018:.012))?!ink?1:0:ink?1:0);}
 return out;
 }
 function features(img){let f=[];for(let y=0;y<8;y++)for(let x=0;x<8;x++){let v=0;for(let j=0;j<3;j++)for(let i=0;i<3;i++)v+=img[(y*3+j)*N+x*3+i];f.push(v/9);}return f;}
 let rows=[];for(let c=0;c<labels.length;c++){for(let i=0;i<160;i++)rows.push({label:c,seed:10001+c*1000+i,split:"train",pixels:render(labels[c],10001+c*1000+i)});for(let i=0;i<40;i++)rows.push({label:c,seed:900001+c*1000+i,split:"test",pixels:render(labels[c],900001+c*1000+i,true)});}
 let data=rows.filter(r=>r.split==="train").map(r=>({x:features(r.pixels),y:r.label})),test=rows.filter(r=>r.split==="test"),weights=labels.map(()=>Array(D).fill(0)),bias=labels.map(()=>0);
 function probs(x){let z=weights.map((w,k)=>bias[k]+w.reduce((a,b,j)=>a+b*x[j],0)),mx=Math.max(...z),p=z.map(v=>Math.exp(v-mx)),sum=p.reduce((a,b)=>a+b,0);return p.map(v=>v/sum);}
 for(let epoch=0;epoch<100;epoch++){let grad=labels.map(()=>Array(D).fill(0)),gb=labels.map(()=>0);for(const row of data){let p=probs(row.x);for(let k=0;k<labels.length;k++){let e=p[k]-(k===row.y?1:0);gb[k]+=e;for(let j=0;j<D;j++)grad[k][j]+=e*row.x[j];}}for(let k=0;k<labels.length;k++){bias[k]-=1.8*gb[k]/data.length;for(let j=0;j<D;j++)weights[k][j]-=1.8*(grad[k][j]/data.length+.002*weights[k][j]);}}
 let confusion=labels.map(()=>labels.map(()=>0)),correct=0,accepted=0,acceptedCorrect=0;for(const row of test){let p=probs(features(row.pixels)),k=p.indexOf(Math.max(...p));confusion[row.label][k]++;if(k===row.label)correct++;if(p[k]>=.65){accepted++;if(k===row.label)acceptedCorrect++;}}
 const model={format:"cad_symbol_softmax_v1",labels,input_size:N,feature_size:8,weights,bias,confidence_threshold:.65,scope:"Synthetic isolated near-upright vector symbols only; not actual full drawing detection."};
 const report={training_count:data.length,test_count:test.length,correct,accuracy:correct/test.length,accepted,accepted_correct:acceptedCorrect,confusion,labels,scope:"Procedurally generated crop holdout; no real drawing evaluation."};
 return {model,report,rows};
}
const result=train();
const out=process.argv[2]||"/tmp/krafzen-cad-symbol";fs.mkdirSync(out,{recursive:true});
fs.writeFileSync(out+"/cad_symbol_model.json",JSON.stringify(result.model)+"\n");fs.writeFileSync(out+"/cad_symbol_evaluation.json",JSON.stringify(result.report,null,2)+"\n");fs.writeFileSync(out+"/cad_symbol_dataset.jsonl",result.rows.map(r=>JSON.stringify(r)).join("\n")+"\n");console.log(JSON.stringify(result.report));
