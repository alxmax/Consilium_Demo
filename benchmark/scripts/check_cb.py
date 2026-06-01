import sys
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent.parent))
sys.path.insert(0, str(__import__('pathlib').Path(__file__).parent))
from analyze import load_run, proxy_breakdown, proxy_score
from _common import MODES

task = 'code/01_circuit_breaker'
print(f"{'mode':30} {'cost':>8}  {'time':>6}  {'Q':>5}  {'$sc':>5}  {'spd':>5}  proxy")
for m in MODES:
    r = load_run(m, task)
    if r is None:
        print(f"{m:30} MISSING")
        continue
    b = proxy_breakdown(r)
    cost_val = f"${r['cost']:.3f}" if r['cost'] is not None else "$--"
    api_sec  = f"{r['api_ms']/1000:.0f}s" if r['api_ms'] is not None else "--"
    print(f"{m:30} {cost_val:>8}  {api_sec:>6}  {b['quality']:>5.1f}  {b['cost']:>5.1f}  {b['speed']:>5.1f}  {proxy_score(r)}")
