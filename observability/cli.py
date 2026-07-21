from __future__ import annotations
import argparse, json, sys
from .store import SQLiteTraceStore

def main(argv=None) -> int:
    parser=argparse.ArgumentParser(description="Local trace inspection (no raw content)"); sub=parser.add_subparsers(dest="command",required=True)
    list_p=sub.add_parser("list-traces"); list_p.add_argument("--status"); list_p.add_argument("--limit",type=int,default=50)
    show=sub.add_parser("show-trace"); show.add_argument("request_id")
    export=sub.add_parser("export-trace"); export.add_argument("request_id")
    sub.add_parser("summarize"); purge=sub.add_parser("purge"); purge.add_argument("--older-than-days",type=int,required=True); purge.add_argument("--confirm",action="store_true")
    args=parser.parse_args(argv); store=SQLiteTraceStore()
    if args.command=="list-traces": output=store.list_traces(status=args.status,limit=args.limit)
    elif args.command in {"show-trace","export-trace"}:
        output=store.get_trace(args.request_id)
        if output is None: print("trace_not_found",file=sys.stderr); return 1
    elif args.command=="summarize": output=store.summarize()
    else:
        if not args.confirm: print("purge_requires_--confirm",file=sys.stderr); return 2
        output={"purged":store.purge_older_than(args.older_than_days)}
    print(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False)); return 0
if __name__=="__main__": raise SystemExit(main())
