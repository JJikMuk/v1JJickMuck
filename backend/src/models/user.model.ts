import { dbpool } from "../config/mariadb";
import { User } from "../types/user.type";

class UsersModel {
    static async getUserIdByUuid(userUuid: string): Promise<number | null> {
        const connection = await dbpool.getConnection();
        try {
            const rows = await connection.query(
                `SELECT id FROM USERS WHERE uuid = ?`,
                [userUuid]
            );
            if (rows.length > 0) {
                return rows[0].id;
            } else {
                return null;
            }
        } finally {
            connection.release();
        }
    }

    static async getUserWithAllergies(userId: number) {
        const connection = await dbpool.getConnection();
        try {
            // 1. 유저 기본 정보 조회
            const userRows = await connection.query(
                `SELECT uuid, email, name, diet_type, created_at, updated_at
                 FROM USERS
                 WHERE id = ?`,
                [userId]
            );

            if (userRows.length === 0) {
                return null;
            }

            // 2. 유저의 알레르기 정보 조회 (3-way JOIN)
            const allergyRows = await connection.query(
                `SELECT a.id as allergy_id, a.name, a.display_name
                 FROM USER_ALLERGIES ua
                 JOIN ALLERGIES a ON ua.allergy_id = a.id
                 WHERE ua.user_id = ?`,
                [userId]
            );

            // 3. 유저 정보 + 알레르기 배열 합치기
            return {
                ...userRows[0],
                allergies: allergyRows.map((row: any) => ({
                    allergy_id: row.allergy_id,
                    allergy_name: row.name,
                    display_name: row.display_name
                }))
            };
        } finally {
            connection.release();
        }
    }

    static async updateUserProfile(userId: number, name?: string, dietType?: string | null, allergyIds?: number[]) {
        const connection = await dbpool.getConnection();
        try {
            await connection.beginTransaction();

            // 1. name 업데이트
            if (name !== undefined) {
                await connection.query(
                    `UPDATE USERS SET name = ? WHERE id = ?`,
                    [name, userId]
                );
            }

            // 2. diet_type 업데이트
            if (dietType !== undefined) {
                await connection.query(
                    `UPDATE USERS SET diet_type = ? WHERE id = ?`,
                    [dietType, userId]
                );
            }

            // 3. 알레르기 정보 업데이트 (기존 데이터 삭제 후 새로 삽입)
            if (allergyIds !== undefined) {
                // 2-1. 기존 알레르기 정보 삭제
                await connection.query(
                    `DELETE FROM USER_ALLERGIES WHERE user_id = ?`,
                    [userId]
                );

                // 2-2. 새로운 알레르기 정보 삽입
                if (allergyIds.length > 0) {
                    const placeholders = allergyIds.map(() => '(?, ?)').join(', ');
                    const values = allergyIds.flatMap(allergyId => [userId, allergyId]);
                    await connection.query(
                        `INSERT INTO USER_ALLERGIES (user_id, allergy_id) VALUES ${placeholders}`,
                        values
                    );
                }
            }

            await connection.commit();
            return true;
        } catch (error) {
            await connection.rollback();
            throw error;
        } finally {
            connection.release();
        }
    }
}

export default UsersModel;