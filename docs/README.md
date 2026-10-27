# KG 101

เอกสารชุดนี้อธิบาย Knowledge Graph (KG) ตั้งแต่พื้นฐาน จนถึงการทำงานของโค้ดใน repo นี้ อ่านตามลำดับได้เลย

| # | หัวข้อ | อ่านแล้วจะเข้าใจ |
|---|---|---|
| 1 | [Knowledge Graph คืออะไร](01-what-is-kg.md) | node, edge, triple, ontology และทำไมต้องเก็บข้อมูลเป็นกราฟ |
| 2 | [Pipeline ใน repo นี้](02-pipeline.md) | ข้อความ → triples → กราฟ → คำตอบ ทีละขั้นพร้อมโค้ด |
| 3 | [GraphRAG vs Vector RAG](03-graphrag-vs-rag.md) | multi-hop คืออะไร และเมื่อไหร่ควรใช้กราฟ |
| 4 | [ข้อจำกัดและสิ่งที่ควรทำต่อ](04-limitations.md) | ปัญหาจริงที่เจอในกราฟตัวอย่าง และวิธีแก้ |

ตัวอย่างทั้งหมดมาจาก [data/sample.txt](../data/sample.txt) (สถานที่ท่องเที่ยว เทศกาล และมรดกโลกของไทย) และผลลัพธ์จริงใน [data/graph.json](../data/graph.json) ถ้ารันเองแล้วผลไม่ตรงทุกตัวอักษรก็ไม่แปลก เพราะ LLM ให้ผลไม่เหมือนกันทุกรอบ

## ลองไปพร้อมกับอ่าน

```bash
uv sync
uv run main.py ingest data/sample.txt --reset   # สร้างกราฟ
uv run main.py stats                            # ดู entity ที่เชื่อมโยงมากที่สุด
uv run main.py viz                              # เปิด data/graph.html
uv run main.py ask "ประเพณีที่ตรงกับยี่เป็งมีต้นกำเนิดที่จังหวัดใด" -v
```

ต้องมี [Ollama](https://ollama.com) ที่รันอยู่ ส่วน model ที่ใช้เปลี่ยนได้ด้วย `KG_MODEL=...`
