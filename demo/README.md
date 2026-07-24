# Demo

A narrated walkthrough of the Legal Judgments KG on a fast, real subset.

```bash
python -m demo.demo
```

Record / regenerate the asciinema cast + gif:
```bash
asciinema rec --overwrite --cols 92 --rows 32 --idle-time-limit 2.0 \
  -c "bash -c 'python -m demo.demo'" demo/legal-judgments.cast
agg demo/legal-judgments.cast demo/legal-judgments.gif
```
