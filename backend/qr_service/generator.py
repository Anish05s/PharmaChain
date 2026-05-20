from pathlib import Path
import qrcode

QR_DIR = Path(__file__).resolve().parent.parent / "static" / "qr"


def ensure_qr_dir() -> None:
    QR_DIR.mkdir(parents=True, exist_ok=True)


def generate_shipment_qr(shipment_id: str) -> str:
    """Encode shipment ID only; save PNG under static/qr/. Returns relative URL path."""
    ensure_qr_dir()
    img = qrcode.make(shipment_id)
    filename = f"{shipment_id}.png"
    img.save(QR_DIR / filename)
    return f"/static/qr/{filename}"
