from sqlmodel import Session, select

from app.db.models import Record, Task
from app.db.session import get_engine, init_db


def test_record_persists_under_task(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    init_db()
    with Session(get_engine()) as session:
        task = Task(kind="poi", status="pending", source_filename="a.csv", total=1)
        session.add(task)
        session.commit()
        session.refresh(task)
        session.add(Record(task_id=task.id, query_name="越秀公园", poi_id="B00140BNNF", aoi_status="pending"))
        session.commit()
        got = session.exec(select(Record).where(Record.task_id == task.id)).one()
    assert got.query_name == "越秀公园"
    assert got.aoi_status == "pending"
    assert got.selected is False
