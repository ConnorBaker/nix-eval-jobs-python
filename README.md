# `nix-eval-jobs-python`

Like `nix-eval-jobs`, but worse.

Aside from being written in Python, the main difference with `nix-eval-jobs` is that this script does not have shared worker memory. As a consequence, it is much, much slower, but it can be used to get the cost of evaluating a single attribute.

TODO:

- Fix flickering when logging output caused by multiple processes writing to stdout
- Docs?

```console
$ nix run .# -- --jobs 1 --flakeref github:NixOS/nixpkgs --attr-path python3Packages
WARNING  Waiting for futures                                                                                                                                                                                                                        main.py:158
{"stats":{"cpuTime":0.2533569931983948,"envs":{"bytes":11550776,"elements":872415,"number":571432},"gc":{"cycles":0,"heapSize":402915328,"totalBytes":189733056},"list":{"bytes":1422664,"concats":31739,"elements":177833},"nrAvoided":692876,"nrExprs":264426,"nrFunctionCalls":499775,"nrLookups":272234,"nrOpUpdateValuesCopied":4904896,"nrOpUpdates":68429,"nrPrimOpCalls":325477,"nrThunks":1173281,"sets":{"bytes":97585184,"elements":5982244,"number":116830},"sizes":{"attr":16,"bindings":16,"env":8,"value":24},"symbols":{"bytes":447327,"number":43072},"time":{"cpu":0.2533569931983948,"gc":0.0,"gcFraction":0.0},"values":{"bytes":48005928,"number":2000247}},"stderr":"warning: failed to perform a full GC before reporting stats\n","value":{"attr":"python3Packages.APScheduler","attrPath":["python3Packages","APScheduler"],"include":true,"name":"python3.12-apscheduler-3.10.4","drvPath":"/nix/store/fw8isxgknq0akjh881nw2znc2f05wfk4-python3.12-apscheduler-3.10.4.drv","system":"x86_64-linux","recurse":false}}
{"stats":{"cpuTime":0.14904800057411194,"envs":{"bytes":5536144,"elements":417405,"number":274613},"gc":{"cycles":0,"heapSize":402915328,"totalBytes":118770384},"list":{"bytes":708600,"concats":10164,"elements":88575},"nrAvoided":353668,"nrExprs":177622,"nrFunctionCalls":231825,"nrLookups":140922,"nrOpUpdateValuesCopied":3409183,"nrOpUpdates":26951,"nrPrimOpCalls":186759,"nrThunks":686119,"sets":{"bytes":66141120,"elements":4080333,"number":53487},"sizes":{"attr":16,"bindings":16,"env":8,"value":24},"symbols":{"bytes":383605,"number":36905},"time":{"cpu":0.14904800057411194,"gc":0.0,"gcFraction":0.0},"values":{"bytes":28754112,"number":1198088}},"stderr":"warning: failed to perform a full GC before reporting stats\n","value":{"attr":"python3Packages.BTrees","attrPath":["python3Packages","BTrees"],"include":true,"name":"python3.12-btrees-6.1","drvPath":"/nix/store/cb7nama95wqk8x9abn54zxajklsn4sfa-python3.12-btrees-6.1.drv","system":"x86_64-linux","recurse":false}}
{"stats":{"cpuTime":0.1479180008172989,"envs":{"bytes":5417192,"elements":408460,"number":268689},"gc":{"cycles":0,"heapSize":402915328,"totalBytes":117979152},"list":{"bytes":693648,"concats":9704,"elements":86706},"nrAvoided":347175,"nrExprs":177315,"nrFunctionCalls":226452,"nrLookups":138308,"nrOpUpdateValuesCopied":3396559,"nrOpUpdates":26101,"nrPrimOpCalls":184245,"nrThunks":678392,"sets":{"bytes":65849584,"elements":4063395,"number":52204},"sizes":{"attr":16,"bindings":16,"env":8,"value":24},"symbols":{"bytes":383589,"number":36904},"time":{"cpu":0.1479180008172989,"gc":0.0,"gcFraction":0.0},"values":{"bytes":28550016,"number":1189584}},"stderr":"warning: failed to perform a full GC before reporting stats\n","value":{"attr":"python3Packages.Babel","attrPath":["python3Packages","Babel"],"include":true,"name":"python3.12-babel-2.16.0","drvPath":"/nix/store/zsqqj0f4v7f2fv48blmhnnlnsbpzyr20-python3.12-babel-2.16.0.drv","system":"x86_64-linux","recurse":false}}
...
```
