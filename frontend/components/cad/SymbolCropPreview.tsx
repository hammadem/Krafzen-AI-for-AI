"use client";
import {useState} from "react";
import {classifyCadSymbol} from "@/lib/models/cadSymbolInference";
export default function SymbolCropPreview(){
 const [result,setResult]=useState<{label:string;confidence:number}|null>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 async function inspect(file:File|null){
  if(!file||busy)return;setBusy(true);setError("");setResult(null);
  try{
   if(!["image/png","image/jpeg","image/webp"].includes(file.type)||file.size>2*1024*1024)throw Error("Select a PNG, JPEG or WebP crop under 2 MB.");
   const bitmap=await createImageBitmap(file);
   try{
    if(bitmap.width<8||bitmap.height<8||bitmap.width>4096||bitmap.height>4096)throw Error("Unsupported image dimensions.");
    const canvas=document.createElement("canvas");canvas.width=24;canvas.height=24;
    const ctx=canvas.getContext("2d");if(!ctx)throw Error("Canvas unavailable");
    ctx.fillStyle="white";ctx.fillRect(0,0,24,24);
    const scale=24/Math.max(bitmap.width,bitmap.height),w=bitmap.width*scale,h=bitmap.height*scale;
    ctx.drawImage(bitmap,(24-w)/2,(24-h)/2,w,h);
    const raw=ctx.getImageData(0,0,24,24).data,pixels=[];
    for(let i=0;i<raw.length;i+=4)pixels.push((raw[i]*.299+raw[i+1]*.587+raw[i+2]*.114)<180?1:0);
    setResult(classifyCadSymbol(pixels));
   }finally{bitmap.close();}
  }catch(e){setError(e instanceof Error?e.message:"Crop could not be read");}finally{setBusy(false);}
 }
 return <section className="rounded-xl border border-white/10 p-4 space-y-2 text-sm">
 <h2 className="font-semibold">Experimental CAD symbol crop</h2>
 <p className="text-xs text-slate-400">Select one tightly isolated, near-upright dark-on-light symbol with some white margin. This synthetic-trained model runs entirely in your browser; no upload, persistence or automatic redline. Real drawing accuracy is unverified. Do not use the result as engineering evidence.</p>
 <label className="block">Symbol crop <input type="file" accept="image/png,image/jpeg,image/webp" disabled={busy} onChange={e=>{const file=e.target.files?.[0]||null;e.currentTarget.value="";void inspect(file);}} className="block"/></label>
 {busy&&<p role="status">Classifying locally…</p>}
 {error&&<p role="alert" className="text-red-300">{error}</p>}
 {result&&<p role="status">{result.label==="unknown"?"Uncertain — no reliable suggestion":`Experimental suggestion: ${result.label.replaceAll("_"," ")}`}. Not verified.</p>}
 </section>;
}
