from flask import Blueprint, jsonify, request

from ..extensions import db
from ..models import (
    Ingredient,
    SOURCE_TYPE_INVENTORY_CHECK,
    SOURCE_TYPE_LABELS,
    SOURCE_TYPE_OPTIONS,
    SOURCE_TYPE_PURCHASE,
    SOURCE_TYPE_STORE_REQUISITION,
    StockRecord,
)

records_bp = Blueprint("records", __name__)

VALID_SOURCE_TYPES = {
    SOURCE_TYPE_PURCHASE,
    SOURCE_TYPE_INVENTORY_CHECK,
    SOURCE_TYPE_STORE_REQUISITION,
}

SOURCE_TYPE_RULES = {
    SOURCE_TYPE_PURCHASE: {
        "allowed_record_types": {"in"},
        "record_type_error": "采购入库只能是入库操作",
        "source_required": True,
        "source_label": "采购单号/供应商",
        "source_placeholder": "请输入采购单号或供应商名称",
    },
    SOURCE_TYPE_INVENTORY_CHECK: {
        "allowed_record_types": {"in", "out"},
        "record_type_error": "盘点调整支持入库或出库操作",
        "source_required": True,
        "source_label": "盘点单号",
        "source_placeholder": "请输入盘点单号",
    },
    SOURCE_TYPE_STORE_REQUISITION: {
        "allowed_record_types": {"out"},
        "record_type_error": "门店领用只能是出库操作",
        "source_required": True,
        "source_label": "领用门店",
        "source_placeholder": "请输入领用门店名称",
    },
}


@records_bp.get("/options")
def get_source_options():
    return {
        "sourceTypes": SOURCE_TYPE_OPTIONS,
        "sourceTypeRules": {
            key: {
                "allowedRecordTypes": list(value["allowed_record_types"]),
                "recordTypeError": value["record_type_error"],
                "sourceRequired": value["source_required"],
                "sourceLabel": value["source_label"],
                "sourcePlaceholder": value["source_placeholder"],
            }
            for key, value in SOURCE_TYPE_RULES.items()
        },
    }


@records_bp.get("")
def list_records():
    record_type = request.args.get("type", "").strip()
    source_type = request.args.get("sourceType", "").strip()
    query = StockRecord.query
    if record_type:
        query = query.filter_by(record_type=record_type)
    if source_type:
        query = query.filter_by(source_type=source_type)
    records = query.order_by(StockRecord.created_at.desc()).all()
    return jsonify([record.to_dict() for record in records])


@records_bp.post("")
def create_record():
    data = request.get_json() or {}
    ingredient = Ingredient.query.get_or_404(data["ingredientId"])
    quantity = float(data["quantity"])
    record_type = data["recordType"]
    source_type = data.get("sourceType")
    source = data.get("source")

    if source_type:
        if source_type not in VALID_SOURCE_TYPES:
            return {"message": "来源类型无效"}, 400
        rules = SOURCE_TYPE_RULES[source_type]
        if record_type not in rules["allowed_record_types"]:
            return {"message": rules["record_type_error"]}, 400
        if rules["source_required"] and (not source or not source.strip()):
            return {"message": f"{SOURCE_TYPE_LABELS[source_type]}需要填写{rules['source_label']}"}, 400

    if record_type == "in":
        ingredient.stock += quantity
    elif record_type == "out":
        if ingredient.stock < quantity:
            return {"message": "库存不足，无法出库"}, 400
        ingredient.stock -= quantity
    else:
        return {"message": "recordType 必须是 in 或 out"}, 400

    record = StockRecord(
        ingredient_id=ingredient.id,
        record_type=record_type,
        quantity=quantity,
        operator=data.get("operator", "系统管理员"),
        source=source,
        source_type=source_type,
        note=data.get("note"),
    )
    db.session.add(record)
    db.session.commit()
    return record.to_dict(), 201
