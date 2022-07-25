package kr.codenu.stockstack.core.stockmarket

import org.ktorm.entity.Entity
import org.ktorm.schema.*

enum class UserType(val value: Int) {
    DUMMY(0),
    HUMAN(1),
    CPU(2);

    companion object {
        fun fromInt(value: Int) = UserType.values().firstOrNull { it.value == value }
    }
}

interface User : Entity<User> {
    val userid: Int
    val username: String
    val usertype: UserType
    val usermoney: Long
}

object Users : Table<User>("t_user") {
    val userid = int("userid").primaryKey()
    val username = varchar("username")
    val usertype = int("usertype")
    val usermoney = long("usermoney")
}

interface UserAsset : Entity<UserAsset> {
    val userid: Int
    val assetid: Int
    val assetamount: Long
    val assetinitialvalue: Long
}

object UserAssets : Table<UserAsset>("t_userasset") {
    val userid = int("userid")
    val assetid = int("assetid")
    val assetamount = long("assetamount")
    val assetinitialvalue = long("assetinitialvalue")
}

interface LoginDiscord : Entity<LoginDiscord> {
    val userid: Int
    val discordid: Long
}

object LoginDiscords : Table<LoginDiscord>("t_logindiscord") {
    val userid = int("userid")
    val discordid = long("discordid")
}
