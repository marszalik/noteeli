"""draw.io diagrams (.drawio / .dio) open in the embedded draw.io editor."""
from pathlib import Path

import pytest

from test_workspace_service import build_service

XML = (
    '<mxfile><diagram name="Page-1" id="a"><mxGraphModel><root><mxCell id="0"/>'
    '<mxCell id="1" parent="0"/><mxCell id="2" value="Hello" style="rounded=1;" vertex="1" parent="1">'
    '<mxGeometry x="120" y="120" width="120" height="60" as="geometry"/></mxCell></root></mxGraphModel></diagram></mxfile>'
)


@pytest.mark.parametrize("name", ["plan.drawio", "plan.dio", "PLAN.DRAWIO"])
def test_drawio_files_open_as_editable_drawio(tmp_path: Path, name: str):
    root = tmp_path / "vault"
    root.mkdir()
    (root / name).write_text(XML, encoding="utf-8")
    doc = build_service(root).read_document(name)
    assert doc.file_type == "drawio" and doc.editable and doc.content == XML


def test_drawio_xml_round_trips_through_save(tmp_path: Path):
    root = tmp_path / "vault"
    root.mkdir()
    service = build_service(root)
    created = service.create_item("", "schemat.drawio", "file")
    assert created.path.endswith("schemat.drawio")
    service.save_document(created.path, XML)
    assert (root / created.path).read_text(encoding="utf-8") == XML
    assert service.read_document(created.path).file_type == "drawio"
