"""evaluate.py : measures the Smart Email Reply Suggester (run: python evaluate.py)
1) Intent-detection accuracy / precision / recall / F1 / confusion matrix
2) Output-format checks on every generated reply set (3 replies, correct
   greeting to the sender, sign-off with the user's name)
Uses reply_engine.detect_intent and suggest_replies unchanged."""
import json, re, time
from reply_engine import detect_intent, suggest_replies, MockBackend

LABELS = ["meeting", "deadline", "complaint", "thanks", "general enquiry"]

# ---- Set A: keyword-style emails  [email text, expected intent] ----
A = [
 ("Hi Priya,\nCan we schedule a meeting tomorrow to discuss the project?\nRegards,\nRahul", "meeting"),
 ("Hello,\nAre you available for a call on Monday morning?\nThanks,\nAnil", "meeting"),
 ("Hi,\nLet us catch up this week over coffee.\nBest,\nMeena", "meeting"),
 ("Dear Priya,\nPlease schedule a review meeting with the design team.\nRegards,\nKiran", "meeting"),
 ("Hi,\nI would like to set up a call to go over the budget.\nCheers,\nSuresh", "meeting"),
 ("Hello Priya,\nIs Thursday afternoon available for a quick meeting?\nRegards,\nLatha", "meeting"),
 ("Hi,\nCan we schedule the client presentation for next week?\nThanks,\nRavi", "meeting"),
 ("Hi Priya,\nWhen are you available for the project meeting?\nBest,\nDeepak", "meeting"),
 ("Hello Priya,\nThe report deadline is this Friday. Please submit it on time.\nThanks,\nAnil", "deadline"),
 ("Hi,\nThe assignment is due tomorrow, please send it.\nRegards,\nMohan", "deadline"),
 ("Dear Priya,\nKindly submit the invoice by Friday.\nRegards,\nKavya", "deadline"),
 ("Hi,\nWe need the final draft ASAP.\nThanks,\nNaveen", "deadline"),
 ("Hello,\nReminder: the form submission deadline is 5 PM today.\nRegards,\nSita", "deadline"),
 ("Hi Priya,\nThe project is due next Monday, please confirm.\nBest,\nGopal", "deadline"),
 ("Dear Priya,\nPlease submit your timesheet before the deadline.\nRegards,\nHari", "deadline"),
 ("Hello,\nTax documents are due on the 30th. Submit them soon.\nThanks,\nRekha", "deadline"),
 ("Hi,\nMy order is not working and I am disappointed. I want a refund.\nRegards,\nSneha", "complaint"),
 ("Hello,\nI have a complaint about the delivery service.\nRegards,\nVikram", "complaint"),
 ("Hi,\nThere is an issue with my account login.\nThanks,\nAsha", "complaint"),
 ("Dear Support,\nI am disappointed with the product quality.\nRegards,\nBharat", "complaint"),
 ("Hi,\nPlease process my refund for the damaged item.\nThanks,\nLakshmi", "complaint"),
 ("Hello,\nThe app is not working since yesterday.\nRegards,\nPrasad", "complaint"),
 ("Hi,\nI want to raise a complaint about the billing error.\nRegards,\nUma", "complaint"),
 ("Hello,\nThe laptop screen has an issue and I need a refund.\nThanks,\nRaju", "complaint"),
 ("Hi Priya,\nThank you for your help with the presentation.\nBest,\nNisha", "thanks"),
 ("Hello,\nThanks a lot for the quick support.\nRegards,\nArjun", "thanks"),
 ("Dear Priya,\nI really appreciate your guidance this semester.\nRegards,\nTeja", "thanks"),
 ("Hi,\nThank you so much for the gift.\nCheers,\nPooja", "thanks"),
 ("Hello Priya,\nThanks for attending our event.\nBest,\nManoj", "thanks"),
 ("Hi,\nWe appreciate your prompt reply.\nRegards,\nSindhu", "thanks"),
 ("Dear Priya,\nThank you for the recommendation letter.\nRegards,\nVenu", "thanks"),
 ("Hi,\nMany thanks for the feedback on my report.\nBest,\nJyothi", "thanks"),
 ("Hi Priya,\nCould you share the course fee details?\nRegards,\nAmit", "general enquiry"),
 ("Hello,\nWhat are the opening hours of your office?\nThanks,\nBhavya", "general enquiry"),
 ("Hi,\nPlease send me the syllabus for the new semester.\nRegards,\nChandra", "general enquiry"),
 ("Dear Priya,\nDo you offer internships for final-year students?\nRegards,\nSai", "general enquiry"),
 ("Hello,\nWhere can I find the admission brochure?\nRegards,\nDivya", "general enquiry"),
 ("Hi,\nWhich documents are needed for registration?\nBest,\nGanesh", "general enquiry"),
 ("Hello Priya,\nHow do I reset the portal password?\nRegards,\nIndu", "general enquiry"),
 ("Hi,\nCan you tell me the price of the premium plan?\nThanks,\nKeerthi", "general enquiry"),
]
# ---- Set B: conversational emails written without the stored keywords ----
B = [
 ("Hey Priya,\nFancy sitting down together sometime next week to go through the plan?\nBest,\nRahul", "meeting"),
 ("Hi,\nWould Wednesday evening work for you to talk about the launch?\nRegards,\nAnita", "meeting"),
 ("Hello Priya,\nLet's find a time to sit together and plan the trip.\nThanks,\nKarthik", "meeting"),
 ("Hi,\nI would love to discuss the proposal with you in person.\nCheers,\nSunil", "meeting"),
 ("Hi Priya,\nPlease get the slides to me before the end of the week.\nRegards,\nMadhu", "deadline"),
 ("Hello,\nWe must have the report in our hands by tomorrow noon.\nThanks,\nPallavi", "deadline"),
 ("Hi,\nThe client is waiting, so we need your part finished quickly.\nBest,\nRoshan", "deadline"),
 ("Hello Priya,\nCould you wrap up the draft before Thursday?\nRegards,\nTara", "deadline"),
 ("Hi,\nThe parcel came broken and nobody is replying to me.\nRegards,\nSneha", "complaint"),
 ("Hello,\nI paid twice for the same subscription and want my money back.\nThanks,\nImran", "complaint"),
 ("Hi,\nYour technician never turned up even after I waited all day.\nRegards,\nSaritha", "complaint"),
 ("Hello,\nThe website keeps crashing whenever I try to pay.\nRegards,\nDinesh", "complaint"),
 ("Hi Priya,\nYou really made my week easier, I am very grateful.\nBest,\nNandini", "thanks"),
 ("Hello,\nI am so glad you stayed back to help me yesterday.\nRegards,\nVarun", "thanks"),
 ("Hi,\nYour advice saved me hours of work. Much obliged!\nCheers,\nPrem", "thanks"),
 ("Hello Priya,\nIt meant a lot that you came to the ceremony.\nBest,\nSwathi", "thanks"),
 ("Hi,\nI was wondering how long the visa process usually takes.\nRegards,\nFarhan", "general enquiry"),
 ("Hello Priya,\nCould you let me know if the library is open on Sundays?\nThanks,\nGeeta", "general enquiry"),
 ("Hi,\nI am new here and unsure where to collect my ID card.\nRegards,\nTarun", "general enquiry"),
 ("Hello,\nIs there a student discount on the annual pass?\nBest,\nRamya", "general enquiry"),
]

def run_set(data):
    rows, lat = [], 0.0
    for text, exp in data:
        t0 = time.perf_counter(); got = detect_intent(text); lat += time.perf_counter() - t0
        rows.append({"q": text.split("\n")[1][:70], "exp": exp, "got": got, "ok": got == exp})
    return rows, lat / len(data) * 1000

rA, msA = run_set(A); rB, msB = run_set(B)
allr = rA + rB
n = len(allr); ok = sum(r["ok"] for r in allr)
cm = {a: {b: 0 for b in LABELS} for a in LABELS}
for r in allr: cm[r["exp"]][r["got"]] += 1
per = {}
for c in LABELS:
    tp = cm[c][c]; fp = sum(cm[x][c] for x in LABELS if x != c); fn = sum(cm[c][x] for x in LABELS if x != c)
    p = tp / (tp + fp) if tp + fp else 0; r = tp / (tp + fn) if tp + fn else 0
    f = 2 * p * r / (p + r) if p + r else 0
    per[c] = dict(p=p, r=r, f=f, sup=tp + fn)
mac = {k: sum(per[c][k] for c in LABELS) / len(LABELS) for k in "prf"}

# ---- output-format checks on every email (MockBackend, same JSON schema as Claude) ----
fmt_ok = greet_ok = sign_ok = 0
for text, _ in A + B:
    res = suggest_replies(text, "Professional", "Priya", backend=MockBackend())
    reps = res["replies"]
    fmt_ok += (len(reps) == 3 and all(x["body"].strip() for x in reps))
    sender = re.search(r"\n([A-Z][a-z]+)\s*$", text.strip()).group(1)
    greet_ok += all(("Dear " + sender) in x["body"] for x in reps)
    sign_ok += all(x["body"].rstrip().endswith("Priya") for x in reps)

print(f"Intent accuracy: {100*ok/n:.1f}%  ({ok}/{n})")
for name, rows, ms in (("A keyword-style", rA, msA), ("B conversational", rB, msB)):
    k = sum(r["ok"] for r in rows)
    print(f"Set {name:17s}: {k}/{len(rows)} correct = {100*k/len(rows):.1f}%   avg {ms:.4f} ms")
print(f"Macro P/R/F1: {mac['p']:.3f} {mac['r']:.3f} {mac['f']:.3f}\n")
print(f"{'Class':16s}{'Prec':>7s}{'Rec':>7s}{'F1':>7s}{'Sup':>5s}")
for c in LABELS: print(f"{c:16s}{per[c]['p']:7.3f}{per[c]['r']:7.3f}{per[c]['f']:7.3f}{per[c]['sup']:5d}")
print("\nConfusion matrix (rows = expected, columns = predicted)")
print(" "*16 + "".join(f"{l[:9]:>10s}" for l in LABELS))
for a in LABELS: print(f"{a:16s}" + "".join(f"{cm[a][b]:10d}" for b in LABELS))
print(f"\nOutput-format checks over {n} emails: 3 non-empty replies {fmt_ok}/{n} | "
      f"greets sender {greet_ok}/{n} | signed with user name {sign_ok}/{n}")
print()
for r in allr:
    if not r["ok"]: print("MISS", repr(r["q"]), "exp", r["exp"], "got", r["got"])
json.dump(dict(acc=ok/n, n=n, setA=sum(r["ok"] for r in rA), setB=sum(r["ok"] for r in rB),
               cm=cm, per=per, macro=mac, ms=[msA, msB], fmt=[fmt_ok, greet_ok, sign_ok]),
          open("results.json", "w"), indent=1)
