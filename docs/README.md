# KG 101

เอกสารชุดนี้อธิบาย Knowledge Graph (KG) ตั้งแต่พื้นฐาน จนถึงการทำงานของโค้ดใน repo นี้ อ่านตามลำดับได้เลย

| # | หัวข้อ | อ่านแล้วจะเข้าใจ |
|---|---|---|
| 1 | [Knowledge Graph คืออะไร](01-what-is-kg.md) | node, edge, triple, ontology และทำไมต้องเก็บข้อมูลเป็นกราฟ |
| 2 | [Pipeline ใน repo นี้](02-pipeline.md) | ข้อความ → triples → กราฟ → คำตอบ ทีละขั้นพร้อมโค้ด |
| 3 | [GraphRAG vs Vector RAG](03-graphrag-vs-rag.md) | multi-hop คืออะไร, service ของแต่ละแบบ (embedding, reranker, graph DB …) และเมื่อไหร่ควรใช้กราฟ |
| 4 | [ข้อจำกัดและสิ่งที่ควรทำต่อ](04-limitations.md) | ปัญหาจริงที่เจอในกราฟตัวอย่าง และวิธีแก้ |
| 5 | [เริ่มทำ KG ของตัวเอง](05-start-your-own.md) | สำหรับคนมีไอเดีย: ต้องเตรียมคำถาม ข้อมูล ontology อะไร รูปแบบไฟล์แต่ละไฟล์ |
| 6 | [ลงมือทำ: ระบบค้าปลีกตั้งแต่ต้นจนจบ](06-walkthrough.md) | 8 ขั้น ใครทำอะไร รันคำสั่งไหน ควรเห็นผลอะไร และตอบผิดแล้วแก้ตรงไหน (ตัวอย่างใน [examples/retail-demo/](../examples/retail-demo/) รันได้จริง) |

> **ไม่ได้เขียนโค้ดเอง?** อ่านบทที่ 1 → 5 → 6 ได้เลย

บทที่ 1–4 ใช้ตัวอย่างจาก [examples/thai-tourism/sample.txt](../examples/thai-tourism/sample.txt) (สถานที่ท่องเที่ยว เทศกาล และมรดกโลกของไทย) ส่วนบทที่ 5–6 ใช้ข้อมูลสมมติระบบค้าปลีกใน [examples/retail-demo/](../examples/retail-demo/) ผลลัพธ์ที่แสดงในเอกสารมาจากการรันจริง ถ้ารันเองแล้วผลไม่ตรงทุกตัวอักษรก็ไม่แปลก เพราะ LLM ให้ผลไม่เหมือนกันทุกรอบ

## ลองไปพร้อมกับอ่าน

```bash
uv sync
uv run main.py ingest examples/thai-tourism/sample.txt --reset   # สร้างกราฟ
uv run main.py stats                            # ดู entity ที่เชื่อมโยงมากที่สุด
uv run main.py viz                              # เปิด examples/thai-tourism/graph.html
uv run main.py ask "ประเพณีที่ตรงกับยี่เป็งมีต้นกำเนิดที่จังหวัดใด" -v
```

ต้องมี [Ollama](https://ollama.com) ที่รันอยู่ ส่วน model ที่ใช้เปลี่ยนได้ด้วย `KG_MODEL=...`
