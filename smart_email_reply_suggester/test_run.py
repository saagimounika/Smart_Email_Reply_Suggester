from reply_engine import suggest_replies, build_prompt, MockBackend
samples = [
 ("Hi Priya,\nCan we schedule a meeting tomorrow to discuss the project? Let me know when you are available.\nRegards,\nRahul", "Professional"),
 ("Hello Priya,\nThe report deadline is this Friday. Please submit it on time.\nThanks,\nAnil", "Friendly"),
 ("Hi,\nMy order is not working and I am disappointed. I want a refund.\nRegards,\nSneha", "Concise"),
]
for i,(mail,tone) in enumerate(samples,1):
    print("="*60); print(f"TEST {i}  | Tone: {tone}"); print("="*60)
    print("INPUT EMAIL:\n"+mail+"\n")
    r = suggest_replies(mail, tone, "Priya", backend=MockBackend())
    print("Detected intent:", r["intent"], "| Engine:", r["backend"])
    for j,x in enumerate(r["replies"],1):
        print(f"\n--- Option {j} ({x['style']}) ---\n{x['body']}")
    print()
print("PROMPT SENT TO MODEL (test 1):\n"+build_prompt(samples[0][0], "Professional", "Priya"))
try: suggest_replies("   ", backend=MockBackend())
except ValueError as e: print("\nEdge case (empty input) ->", e)
