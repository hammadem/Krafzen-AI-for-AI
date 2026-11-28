import { NextResponse } from "next/server";

// Never fetch arbitrary caller-controlled URLs from the application server.
export function GET() {
    return NextResponse.json({error:"Server-side image proxy disabled. Use an authorized image download."}, {status:410,headers:{"Cache-Control":"no-store"}});
}
