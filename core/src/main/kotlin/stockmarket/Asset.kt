package kr.codenu.stockstack.core.stockmarket

import org.ktorm.entity.Entity
import org.ktorm.schema.*

enum class AssetType(val value: Int) {
    STOCK(0),
    ;

    companion object {
        fun fromInt(value: Int) = UserType.values().firstOrNull { it.value == value }
    }
}

interface Asset : Entity<Asset> {
    val assetid: Int
    val assettype: AssetType
    val assetamount: Int
}

object Assets : Table<Nothing>("t_asset") {
    val assetid = int("assetid").primaryKey()
    val assettype = int("assettype")
    val assetamount = long("assetamount")
}