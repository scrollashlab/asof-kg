"""Exhaustive no-leakage check for the as-of query.

For every record time k and valid time v on a grid built from each interval boundary in the worked example
(the boundary itself and one second either side), the script runs the same SPARQL as-of query used in
asof_query.py for every subject and checks three things:
  1. No returned statement entered the record after k (no future knowledge at time k).
  2. No returned statement had been withdrawn or superseded in the record at or before k.
  3. The SPARQL result equals an independent Python implementation of the same interval rule.
Exits non-zero on any failure.
"""
import os, sys, datetime as dt, rdflib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__))); os.chdir(ROOT)
g = rdflib.Graph(); g.parse('ontology/asof-kg.ttl')
P = '''PREFIX asof: <https://w3id.org/asof-kg/ontology#>
PREFIX time: <http://www.w3.org/2006/time#>
PREFIX biolink: <https://w3id.org/biolink/vocab/>
'''
ALL = P + '''SELECT ?s ?subj ?rb ?re ?vb ?ve WHERE {
  ?s biolink:subject ?subj ; asof:hasRecordTime ?rt ; asof:hasValidTime ?vt .
  ?rt time:hasBeginning/time:inXSDDateTimeStamp ?rb . OPTIONAL { ?rt time:hasEnd/time:inXSDDateTimeStamp ?re }
  ?vt time:hasBeginning/time:inXSDDateTimeStamp ?vb . OPTIONAL { ?vt time:hasEnd/time:inXSDDateTimeStamp ?ve } }'''
# Same filters as scripts/asof_query.py, written for a bound subject.
ASOF = P + '''PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?s WHERE {
  ?s biolink:subject ?subj ; asof:hasRecordTime ?rt ; asof:hasValidTime ?vt .
  ?rt time:hasBeginning/time:inXSDDateTimeStamp ?rb . OPTIONAL { ?rt time:hasEnd/time:inXSDDateTimeStamp ?re }
  ?vt time:hasBeginning/time:inXSDDateTimeStamp ?vb . OPTIONAL { ?vt time:hasEnd/time:inXSDDateTimeStamp ?ve }
  FILTER (xsd:dateTime(STR(?rb)) <= ?k && (!BOUND(?re) || ?k < xsd:dateTime(STR(?re))))
  FILTER (xsd:dateTime(STR(?vb)) <= ?v && (!BOUND(?ve) || ?v < xsd:dateTime(STR(?ve)))) }'''
ts = lambda lit: None if lit is None else dt.datetime.fromisoformat(str(lit))
rows = [(r.s, r.subj, ts(r.rb), ts(r.re), ts(r.vb), ts(r.ve)) for r in g.query(ALL)]
if not rows: sys.exit('no statements found')
subjects = sorted({r[1] for r in rows})
sec = dt.timedelta(seconds=1)
rgrid = sorted({b + d for r in rows for b in (r[2], r[3]) if b for d in (-sec, dt.timedelta(0), sec)})
vgrid = sorted({b + d for r in rows for b in (r[4], r[5]) if b for d in (-sec, dt.timedelta(0), sec)})
def reference(subj, k, v):  # independent implementation: half-open intervals [begin, end)
    return {s for s, sj, rb, re, vb, ve in rows if sj == subj and rb <= k and (re is None or k < re) and vb <= v and (ve is None or v < ve)}
info = {r[0]: r for r in rows}
lit = lambda t: rdflib.Literal(t.isoformat(), datatype=rdflib.XSD.dateTime)
n = fails = 0
for subj in subjects:
    for k in rgrid:
        for v in vgrid:
            got = {r.s for r in g.query(ASOF, initBindings={'subj': subj, 'k': lit(k), 'v': lit(v)})}
            n += 1
            for s in got:
                _, _, rb, re, _, _ = info[s]
                if rb > k: fails += 1; print('LEAK: future statement', s, 'recorded', rb, 'returned as of', k)
                if re is not None and re <= k: fails += 1; print('STALE: withdrawn statement', s, 'ended', re, 'returned as of', k)
            if got != reference(subj, k, v): fails += 1; print('MISMATCH', subj, k, v, sorted(got), sorted(reference(subj, k, v)))
print(f'statements {len(rows)}, subjects {len(subjects)}, record-time cuts {len(rgrid)}, valid-time cuts {len(vgrid)}, queries {n}')
print('leakage check:', 'PASS' if not fails else f'FAIL ({fails})')
sys.exit(1 if fails else 0)
