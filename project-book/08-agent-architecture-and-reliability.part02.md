### דוגמה: בדיקת פעימת־לב של ה־Watchdog

```python
import time

def watchdog_check(last_heartbeat, timeout_sec=180):
    # last_heartbeat: epoch time of the main loop's last signal.
    elapsed = time.time() - last_heartbeat
    if elapsed > timeout_sec:
        # Main loop appears frozen: persist state and shut down cleanly.
        persist_state()        # save game state for later recovery
        controlled_shutdown()  # release MCP connections, close logs
        return "SHUTDOWN"
    return "ALIVE"
```

התהליך משווה את הזמן שחלף מאז פעימת-הלב האחרונה אל סף קבוע. כל עוד הלולאה הראשית פולטת פעימה בקצב סדיר, ה־Watchdog מחזיר `ALIVE` ואינו מתערב. אך אם חלפו יותר מן הסף הקצוב — סימן שהמודל קרס או שהתקשורת נתקעה — הוא משמר את המצב ומבצע כיבוי מבוקר, כך שניתן יהיה להתאושש מאוחר יותר במקום לאבד את המשחק כולו.

---

<!-- source-pdf-page: 84 -->

### חיבור לקורס
רעיון המתזמר כשער-כניסה יחיד לתת-סוכנים איננו חדש לכם. בהרצאה ,שעסקה בסוכנים ותת-סוכנים, _I אורקסטרציה של סוכניA_ של הקורס L05 (מאציל עבודה לקבוצת תת-סוכניםOrchestratorראיתם כיצד סוכן-על ) (,Commands(ופקודות )Skillsהוא מפעיל מיומנויות ) דרך שער יחיד: ומרכז את כל זרימת המידע ביניהם במקום שכל רכיב יפנה ישירות לרעהו. של סוכן המשחק הוא בדיוק אותו דפוס, מוקשח לתנאי Orchestratorה,מודול ההחלטה, מנהלMCPתת-המערכות )מחבר ה- משחק תחרותי: היומנים, עוקב-המועדים וכלב-השמירה( הן ה״תת-סוכנים״, וההאצלה דרך שער יחיד — אותה הפרדת אחריות — היא שמאפשרת להחליף, לבדוד ולתקן כל רכיב בנפרד. כיוון ששני הצדדים במשחק בנויים באופן סימטרי, כל אחד מהם מריץ מתזמר ומכונת-מצבים משלו לפי אותו דפוס בדיוק.

**סיכום הפרק 8.5**

תיאום ראינו שסוכן משחק אמין נבנה על שני עמודי-תווך של פיתוח: ואמינות. המתזמר מרכז את כל תת-המערכות מאחורי שער יחיד ומכפיף את מהלך המשחק למכונת מצבים החוסמת מעברים בלתי-חוקיים ומונעת קיפאון. מניחים מראש שהרשת והמודל ייכשלו, WatchdogוהDeadline Trackerדפוסי ה- עם ומספקים ניסיון-חוזר, כיבוי מבוקר ושימור מצב במקום קריסה שקטה. שלד אמין זה בידינו, נפנה בפרק הבא אל השכבה שמעליו — הלוגיקה האסטרטגית שממלאת את מודול ההחלטה בתוכן.

---

[← Chapter 7 — GUI and Replay Simulator](07-gui-and-replay-simulator.md) · [Contents](README.md) · [Chapter 9 — League, Computational Fairness, and Reporting →](09-league-fairness-and-reporting.md)
