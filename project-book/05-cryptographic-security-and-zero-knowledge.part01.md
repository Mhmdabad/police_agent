# Chapter 5 — Cryptographic Security and Zero Knowledge

> **Source:** [Distributed Cops-and-Robbers over a Peer-to-Peer Network, v3.0.0](https://github.com/rmisegal/Game-P2P-Cop-Chase/blob/master/docs/police_thief_p2p.pdf)
> **Physical PDF pages:** 48–56
> **Source SHA-256:** `7c9e1d7527582c3aef9afd71709981cea50ea60b8fabefe85efccab0a5fdd02e`
>
> Curated Markdown transcription for repository-local study. The source PDF remains authoritative; Appendix F is the sole authority for binding quantitative parameters. Hebrew/English bidirectional text, equations, and complex visual layouts may render differently from the PDF.
>
> Copyright © 2026 Dr. Yoram Segal / Gal Technologies Artificial Intelligence Ltd. All rights reserved. Authorized educational use only under the source terms; no commercial use or redistribution.

[← Chapter 4 — Dynamic Pheromones and Collective Memory](04-dynamic-pheromones-and-collective-memory.md) · [Contents](README.md) · [Chapter 6 — Strategy and Decision Making →](06-strategy-and-decision-making.md)

---

<!-- source-pdf-page: 48 -->

## פרק 5 — פרוטוקול אבטחה קריפטוגרפי ואפס־ידיעה
### מטרות הפרק 5.1
בסיום פרק זה תדעו: מדוע רשת עמית-לעמית ללא מנהל משחק אובייקטיבי המבוסס על CommitReveal כיצד מנגנון סובלת מפיתוי מובנה לרמאות; (הופך את הרמאות לבלתי-אפשרית מבחינה מעשית;Hashפונקציות גיבוב ) כיצד ביקורת הדדית של יומני המשחק מגלה כל זיוף בדיעבד; וכיצד הצהרת חומרה חתומה ב״צעד-אפס״ מבטיחה הוגנות חישובית בין מתחרים בעלי מכונות שונות בתכלית.

---

<!-- source-pdf-page: 49 -->

### The Temptation to Cheat הפיתוי לרמות ברשת נטולת-שופט 5.2
דמיינו משחק שחמט שבו אין לוח פיזי משותף ואין שופט המשגיח על הכללים; במערכת כל שחקן מנהל עותק פרטי של הלוח ומדווח לרעהו על מהלכיו. (שבה שני הסוכנים מדבריםP2Pמבוזרת מסוג זה — רשת עמית-לעמית ) ,בלא מנהל משחק אובייקטיבי — נולדFastMCP ישירות זה עם זה מעל שרת _מסע_ פיתוי מובנה לרמאות. שלושה סוגי הונאה מאיימים על שלמות המרוץ: שנחשף מהלך היריב; _לאחר_ — שינוי של מהלך שכבר בוצע; שינוי מהלך _בזמן_ והתכחשות למיקום או להצהרה קודמים. כל עוד כל צד הוא גם השחקן וגם רושם-הפרוטוקול של עצמו, אין דבר המונע ממנו לכתוב מחדש את ההיסטוריה

לטובתו.

במקום להסתמך על אמון, המערכת הפתרון אינו משפטי אלא מתמטי. המבוסס על פונקציות גיבוב קריפטוגרפיות. CommitReveal נשענת על מנגנון ,הוא זה: מחייבים[18] רעיון היסוד, המוכר בספרות כ״הטלת מטבע בטלפון״ על החלטתו בעודה חתומה וסתומה, ורק לאחר שהיריב נעל את _התחייב_ כל צד ל התחייבותו-שלו — נחשפת ההחלטה. כך נמנעת האפשרות לשנות בחירה לאחר מעשה, שכן השינוי היה שובר את החתימה הקריפטוגרפית שכבר הועברה.

**חיבור לקורס**

,ראיתם כיצד שניL09 ״, בהרצאהAI בקורס ״אורקסטרציה של סוכני וקוראים לכלים חיצוניים — MCP משוחחים זה עם זה מעל AI סוכני שני תהליכים עצמאיים המחליפים הודעות ישירות, בלא רכיב-על מרכזי המפקח עליהם. פרק זה מוסיף לאותה ארכיטקטורה של קריאות-כלים בין (:כאשר אין שרת מרכזי מהימןIntegrity ) _שלמות_ סוכן לסוכן את שכבת ה שמכתיב אמת אחת, הצורך לוודא את יושרתה של תקשורת מבוזרת חייב זהו העיקרון שמבדיל מערכת מבוזרת לנבוע מן הקריפטוגרפיה עצמה. . _אמינה_ ממערכת מבוזרת _שבירה_

---

<!-- source-pdf-page: 50 -->

### CommitReveal over SHA256 מעל CommitReveal מנגנון 5.3
### SHA256
בכל צעד משחק מבצע כל סוכן ארבעה שלבים קריפטוגרפיים מחייבים, לפי שלא ניתן להכחישו או _אירוע מחויב_ שלבים אלו הופכים כל מהלך ל הסדר. לשנותו בדיעבד.

**—מספר חד-פעמי Nonce**

(הוא מחרוזת אקראית ייחודיתNumber used once )קיצור של Nonce הנוצרת מחדש בכל התחייבות. תפקידו כפול: ראשית, הוא מבטיח שגם אם סוכן חוזר על אותה פעולה בדיוק, הגיבוב המתקבל יהיה שונה בכל —ניסיון של (Dictionary Attack ) _התקפת מילון_ שנית, הוא מסכל פעם. היריב לנחש את התוכן הסתום על-ידי גיבוב מוקדם של כל האפשרויות ,מרחב המהלכים הקטן היה מאפשר לפצח כלNonceהסבירות. ללא ה- התחייבות בשבריר שנייה.

**Commit —התחייבות שלב1 5.3.1** המציין Intent הסוכן בוחר את מהלכו הפיזי ואת הרמז שישלח )לרבות דגל ארבעת רכיבי הנתונים ייחודי. Nonce אם הרמז אמיתי או כוזב(, ומגריל הסוכן משגר דרך משורשרים יחד ומקודדים לכדי גיבוב קריפטוגרפי בודד. — לא את תוכנה. _בלבד Hcommit_ את החתימה FastMCPשרת ה-

**חתימת ההתחייבות הקריפטוגרפית**

$$H_{commit}=\operatorname{SHA256}(State \parallel Move \parallel Intent \parallel Nonce)$$

(:הוא מדביק את ייצוגי הבתיםConcatenation ) _שרשור_ הוא אופרטור ה _∥_ הסימן של הרכיבים זה לזה לכדי מחרוזת אחת רציפה, לפני החלת פונקציית הגיבוב. אין הוא חיבור מספרי אלא הצמדה של רצפי-בתים. במימוש הייחוס השרשור )מפתחות ממוינים ומפרידים _JSON סריאליזציה קנונית ל-_ נעשה באמצעות בדיוק; הרשומה הנחתמת בפועל _זהים_ קבועים(, כדי ששני העמיתים יגבבו בתים עשירה מארבעת השדות שכאן, וכוללת גם את הרמז המילולי, סיווג הכוונה, מספר הצעד והתפקיד. משתני הנוסחה מנותחים כך:

---

<!-- source-pdf-page: 51 -->

סיביות המתקבלת 256 מחרוזת בת **—חתימת ההתחייבות.** _Hcommit_ - זוהי ״טביעת האצבע״ של _משמעות מעשית:_ .[19] SHA256 מפונקציית המהלך; היא נשלחת ליריב אך אינה חושפת דבר על תוכנו. - תמונת המצב שעליה מבוסס המהלך, המקבעת את **—מצב הלוח.** _State_ מונעת שימוש חוזר _משמעות מעשית:_ ההתחייבות לצעד משחק ספציפי.

בהתחייבות ישנה בהקשר חדש. המהלך הנבחר )תנועה, הצבת חסם וכדומה(. **—הפעולה הפיזית.** _Move_ - זהו הליבה שאותה מבקשים לנעול מפני שינוי. _משמעות מעשית:_ ערך המציין אם הרמז המילולי הנלווה אמיתי **—דגל הכוונה.** _Intent_ - מחייב את הסוכן להכריז _משמעות מעשית:_ (.lie(או מטעה )truth) מראש על כנותו, כך שלא יוכל לטעון בדיעבד ששיקר ״בכוונה״. _משמעות_ מחרוזת אקראית קריפטוגרפית. **—מספר חד-פעמי.** _Nonce_ - מבטיחה ייחודיות הגיבוב ומסכלת התקפת מילון, כמוסבר _מעשית:_ בהגדרה לעיל.

**Acknowledge, Reveal, Audit —אישור, חשיפה וביקורת 4–שלבים2 5.3.2** לאחר ההתחייבות ממשיך הפרוטוקול בשלושה שלבים נוספים: - היריב מאשר כי קיבל את ההתחייבות וכי הוא **).Acknowledgeאישור (** עליה. אישור זה מונע מן השולח לסגת מהתחייבותו, ובה בעת מבטיח _נעול_

שהחשיפה תתרחש רק כששני הצדדים כבר קיבעו את מהלכיהם. - (ואת המשפטMoveהסוכן שולח ליריב את הפעולה ) **).Revealחשיפה (** בשלב זה, כדי למנוע הנדסה-לאחור של _נשאר חבוי_ Nonceההמילולי.

החתימות בטרם עת.

- רק בתום המשחק כולו נחשפים **).Audit / Final Revealביקורת סופית (** ,לשם ביקורת הדדית מלאה.Nonceכל ערכי ה-

---

<!-- source-pdf-page: 52 -->

<details>
<summary>Figure text extracted from the source PDF</summary>

```text
Cop Thief
Step 1 Commit: Hcommit  only
Step 2 Acknowledge (locked)
Step 3 Reveal: Move + Hint (Nonce hidden)
Reveal: Move + Hint
Step 4 Final Reveal: all Nonces (end of game)
Final Reveal: all Nonces
```

</details>

Com :רצף חילופי ההודעות בין השוטר לגנב לאורך ארבעת שלבי6 איור נחשף אך ורק בשלב Nonce.שימו לב שה-Audit _→_ Reveal _→_ Acknowledge _→_ mit הביקורת הסופי, בתום המשחק.

מימין( וחיצים Thief משמאל, Cop שני קווי-חיים אנכיים ) **מה רואים באיור:** תחילה עוברת אופקיים המתארים את סדר ההודעות מלמעלה למטה. ההתחייבות הסתומה, אחר-כך האישור הנעילה, לאחריו החשיפה ההדדית **כיצד** .Nonceשל המהלכים, ולבסוף — בתום המשחק — חשיפת כל ה- הפרדת הזמן בין ההתחייבות לחשיפה היא הלב הקריפטוגרפי; משנשלח **לפרש: ניתוח ״מה יקרה אם״:** מתמטית אף שתוכנו טרם ידוע. _ננעל_ ,המהלך _Hcommit_ אם סוכן ינסה לחשוף בשלב3מהלך שאינו תואם את ההתחייבות ששלח המקורי _Hcommit_ בשלב1,הגיבוב שיחושב מחדש בשלב הביקורת לא יתאים ל- — והרמאות תיחשף חד-משמעית. היוצר את החתימה, commit() הקוד שלהלן ממחיש את שני קצות המנגנון: להגרלת secrets המשחזר אותה ומשווה. שימו לב לשימוש במודול verify()והצפוי מדי. randomקריפטוגרפי, ולא ב- Nonce

---

<!-- source-pdf-page: 53 -->

### מימוש `commit()` ו־`verify()` מעל SHA-256

```python
import hashlib
import json
import secrets

def commit(state: str, move: str, intent: str) -> tuple[str, str]:
    # Generate a fresh cryptographic nonce (defeats dictionary attacks).
    nonce = secrets.token_hex(16)
    # Serialize the fields as CANONICAL JSON (sorted keys, fixed separators)
    # so BOTH peers hash byte-identical input. The reference code seals a
    # richer record (hint, verdict, step, role, sub_game); the core is shown.
    payload = json.dumps(
        {"state": state, "move": move, "intent": intent, "nonce": nonce},
        sort_keys=True,
        separators=(",", ":"),
    )
    h_commit = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    # Send only h_commit now; keep nonce secret until the final audit.
    return h_commit, nonce

def verify(
    state: str, move: str, intent: str, nonce: str, h_commit: str
) -> bool:
    # Re-synthesize the opponent's hash from the revealed data.
    payload = json.dumps(
        {"state": state, "move": move, "intent": intent, "nonce": nonce},
        sort_keys=True,
        separators=(",", ":"),
    )
    recomputed = hashlib.sha256(payload.encode("utf-8")).hexdigest()
    # Any mismatch proves tampering occurred.
    # The return statement continues on the next physical source page.
```

---

<!-- source-pdf-page: 54 -->

```python
    return secrets.compare_digest(recomputed, h_commit)
