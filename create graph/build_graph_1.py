from neo4j import GraphDatabase
import re
import uuid

# ========= 1. 配置 Neo4j 连接 =========
NEO4J_URI = "neo4j+s://36f08b4f.databases.neo4j.io"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "Z-kmRY5XTupSahevPpRzQZqpRfFcw0ApigFBfDVFyQo"  

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# ========= 2. 解析头部行：工艺｜工序｜【信息类型】 =========
HEADER_RE = re.compile(r"(.+?)｜(.+?)｜【(.+?)】")

def parse_header(line: str):
    """
    输入例如：'冲压工艺｜材料准备｜【定义】'
    输出：('冲压工艺', '材料准备', '定义')
    """
    m = HEADER_RE.match(line.strip())
    if not m:
        return None
    process, stage, info_type = m.groups()
    return process.strip(), stage.strip(), info_type.strip()

# ========= 3. Neo4j 写入函数 =========
def create_text_unit(tx, process, stage, info_type, content):
    """
    在 Neo4j 中：
    - MERGE 一个 PROCESS
    - MERGE 一个 STAGE（带 process_name）
    - CREATE 一个 TEXT_UNIT
    - 建立 HAS_STAGE / ABOUT_PROCESS / ABOUT_STAGE 关系
    """
    tu_id = str(uuid.uuid4())

    tx.run(
        """
        MERGE (p:PROCESS {name: $process})
        MERGE (s:STAGE {name: $stage, process_name: $process})
        CREATE (t:TEXT_UNIT {
            id: $id,
            process: $process,
            stage: $stage,
            info_type: $info_type,
            content: $content
        })
        MERGE (p)-[:HAS_STAGE]->(s)
        MERGE (t)-[:ABOUT_PROCESS]->(p)
        MERGE (t)-[:ABOUT_STAGE]->(s)
        """,
        {
            "id": tu_id,
            "process": process,
            "stage": stage,
            "info_type": info_type,
            "content": content,
        },
    )

def import_txt_to_neo4j(txt_path: str):
    """
    主逻辑：从 txt 文件中读出所有 TextUnit，写入 Neo4j。
    """
    with open(txt_path, "r", encoding="utf-8") as f:
        lines = f.read().splitlines()

    current_process = None
    current_stage = None
    current_info_type = None
    buffer = []

    with driver.session() as session:
        # 为了简单，所有写操作放在一个 write_transaction 里
        def _write_all(tx):
            nonlocal current_process, current_stage, current_info_type, buffer

            for raw in lines:
                line = raw.strip()

                # 忽略空行
                if not line:
                    continue

                # 分隔线 '---'
                if line == "---":
                    # 到一个 block 末尾，flush buffer
                    if (
                        current_process
                        and current_stage
                        and current_info_type
                        and buffer
                    ):
                        content = "\n".join(buffer).strip()
                        create_text_unit(
                            tx,
                            current_process,
                            current_stage,
                            current_info_type,
                            content,
                        )
                    # 清空 buffer，等待下一段
                    buffer = []
                    continue

                # 尝试解析头部
                header = parse_header(line)
                if header:
                    # 进入新的 TextUnit 之前，把旧的 flush 掉
                    if (
                        current_process
                        and current_stage
                        and current_info_type
                        and buffer
                    ):
                        content = "\n".join(buffer).strip()
                        create_text_unit(
                            tx,
                            current_process,
                            current_stage,
                            current_info_type,
                            content,
                        )
                        buffer = []

                    current_process, current_stage, current_info_type = header
                else:
                    # 普通内容行，加入 buffer
                    buffer.append(line)

            # 文件结束后，最后一块也要 flush 一次
            if current_process and current_stage and current_info_type and buffer:
                content = "\n".join(buffer).strip()
                create_text_unit(
                    tx, current_process, current_stage, current_info_type, content
                )

        session.execute_write(_write_all)

    print("导入完成！")

if __name__ == "__main__":
    import_txt_to_neo4j("汽车自动化.txt")
    driver.close()
