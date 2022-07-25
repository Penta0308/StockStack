package kr.codenu.stockstack.core.stockmarket

import kr.codenu.stockstack.core.StockStackApp
import org.ktorm.database.Database
import org.ktorm.dsl.insertAndGenerateKey

object UserManager {
    suspend fun create(username: String, usertype: UserType, usermoney: Long = 0): Int {
        val userid = Database.connect(StockStackApp.datasource).insertAndGenerateKey(Users) {
            set(it.username, username)
            set(it.usertype, usertype.value)
            set(it.usermoney, usermoney)
        }
        return userid as Int
    }

    suspend fun create_discordcredential(userid: Int, discordid: ULong): Int {
        return Database.connect(StockStackApp.datasource).insertAndGenerateKey(LoginDiscords) {
            set(it.userid, userid)
            set(it.discordid, discordid.toLong())  // Intentional Overflow
        } as Int
    }
}