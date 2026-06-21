from datetime import datetime

from ..extensions import db


SOURCE_TYPE_PURCHASE = "purchase"
SOURCE_TYPE_INVENTORY_CHECK = "inventory_check"
SOURCE_TYPE_STORE_REQUISITION = "store_requisition"

SOURCE_TYPE_LABELS = {
    SOURCE_TYPE_PURCHASE: "采购入库",
    SOURCE_TYPE_INVENTORY_CHECK: "盘点调整",
    SOURCE_TYPE_STORE_REQUISITION: "门店领用",
}

SOURCE_TYPE_OPTIONS = [
    {"value": SOURCE_TYPE_PURCHASE, "label": SOURCE_TYPE_LABELS[SOURCE_TYPE_PURCHASE]},
    {"value": SOURCE_TYPE_INVENTORY_CHECK, "label": SOURCE_TYPE_LABELS[SOURCE_TYPE_INVENTORY_CHECK]},
    {"value": SOURCE_TYPE_STORE_REQUISITION, "label": SOURCE_TYPE_LABELS[SOURCE_TYPE_STORE_REQUISITION]},
]


class StockRecord(db.Model):
    __tablename__ = "stock_records"

    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey("ingredients.id"), nullable=False)
    record_type = db.Column(db.String(10), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    operator = db.Column(db.String(40), nullable=False)
    source = db.Column(db.String(80), nullable=True)
    source_type = db.Column(db.String(30), nullable=True)
    note = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ingredient = db.relationship("Ingredient")

    def to_dict(self):
        return {
            "id": self.id,
            "ingredientId": self.ingredient_id,
            "ingredientName": self.ingredient.name if self.ingredient else None,
            "unit": self.ingredient.unit if self.ingredient else None,
            "recordType": self.record_type,
            "quantity": self.quantity,
            "operator": self.operator,
            "source": self.source,
            "sourceType": self.source_type,
            "sourceTypeLabel": SOURCE_TYPE_LABELS.get(self.source_type, "") if self.source_type else "",
            "note": self.note,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
