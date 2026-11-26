import {describe,it,expect} from "vitest";
import {classifyCadSymbol} from "@/lib/models/cadSymbolInference";
describe("CAD symbol crop model",()=>{
 it("abstains on blank and filled crops",()=>{
  expect(classifyCadSymbol(Array(576).fill(0)).label).toBe("unknown");
  expect(classifyCadSymbol(Array(576).fill(1)).label).toBe("unknown");
 });
 it("rejects invalid input",()=>expect(()=>classifyCadSymbol([1])).toThrow());
 it("classifies a centered circular raster as an advisory",()=>{
  const pixels=Array.from({length:576},(_,i)=>Math.abs(Math.hypot((i%24+.5)/12-1,(Math.floor(i/24)+.5)/12-1)-.43)<.06?1:0);
  expect(classifyCadSymbol(pixels).label).toBe("pipe_circle");
 });
});
