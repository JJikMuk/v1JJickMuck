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

    // ============================================
    // 유저 전체 프로필 조회 (RAG API용)
    // ============================================
    static async getUserFullProfile(userUuid: string) {
        const connection = await dbpool.getConnection();
        try {
            // 1. 기본 유저 정보
            const userRows = await connection.query(
                `SELECT id, uuid, email, name, diet_type, height, weight, age_range, gender
                 FROM USERS WHERE uuid = ?`,
                [userUuid]
            );

            if (userRows.length === 0) {
                return null;
            }

            const user = userRows[0];

            // 2. 알레르기 조회
            const allergyRows = await connection.query(
                `SELECT a.id, a.name, a.display_name
                 FROM USER_ALLERGIES ua
                 JOIN ALLERGIES a ON ua.allergy_id = a.id
                 WHERE ua.user_id = ?`,
                [user.id]
            );

            // 🔍 디버깅 로그 추가
            console.log('=== 알레르기 쿼리 결과 ===');
            console.log('user.id:', user.id);
            console.log('allergyRows 타입:', typeof allergyRows);
            console.log('allergyRows:', JSON.stringify(allergyRows, null, 2));
            console.log('========================');

            // 3. 질병 조회
            const diseaseRows = await connection.query(
                `SELECT d.id, d.name, d.display_name
                 FROM USER_DISEASES ud
                 JOIN DISEASES d ON ud.disease_id = d.id
                 WHERE ud.user_id = ?`,
                [user.id]
            );

            // 4. 특수 상태 조회
            const conditionRows = await connection.query(
                `SELECT sc.id, sc.name, sc.display_name
                 FROM USER_SPECIAL_CONDITIONS usc
                 JOIN SPECIAL_CONDITIONS sc ON usc.condition_id = sc.id
                 WHERE usc.user_id = ?`,
                [user.id]
            );

            // null/undefined 값 필터링
            const allergies = Array.isArray(allergyRows) 
                ? allergyRows.map((a: any) => a.display_name).filter((v: any) => v != null)
                : [];
            
            const diseases = Array.isArray(diseaseRows)
                ? diseaseRows.map((d: any) => d.display_name).filter((v: any) => v != null)
                : [];
            
            const specialConditions = Array.isArray(conditionRows)
                ? conditionRows.map((sc: any) => sc.display_name).filter((v: any) => v != null)
                : [];

            return {
                user_id: user.uuid,
                email: user.email,
                name: user.name,
                diet_type: user.diet_type,
                height: user.height,
                weight: user.weight,
                age_range: user.age_range,
                gender: user.gender,
                allergies,
                diseases,
                special_conditions: specialConditions
            };
        } finally {
            connection.release();
        }
    }

    // ============================================
    // 질병 관련 CRUD
    // ============================================

    // 모든 질병 목록 조회
    static async getAllDiseases() {
        const connection = await dbpool.getConnection();
        try {
            const rows = await connection.query(
                'SELECT id, name, display_name FROM DISEASES ORDER BY display_name'
            );
            return rows;
        } finally {
            connection.release();
        }
    }

    // 유저 질병 조회
    static async getUserDiseases(userId: number) {
        const connection = await dbpool.getConnection();
        try {
            const rows = await connection.query(
                `SELECT d.id, d.name, d.display_name
                 FROM USER_DISEASES ud
                 JOIN DISEASES d ON ud.disease_id = d.id
                 WHERE ud.user_id = ?`,
                [userId]
            );
            return rows;
        } finally {
            connection.release();
        }
    }

    // 유저 질병 업데이트 (일괄)
    static async updateUserDiseases(userId: number, diseaseIds: number[]) {
        const connection = await dbpool.getConnection();
        try {
            await connection.beginTransaction();

            // 기존 질병 삭제
            await connection.query(
                'DELETE FROM USER_DISEASES WHERE user_id = ?',
                [userId]
            );

            // 새 질병 추가
            if (diseaseIds.length > 0) {
                const placeholders = diseaseIds.map(() => '(?, ?)').join(', ');
                const values = diseaseIds.flatMap(diseaseId => [userId, diseaseId]);
                await connection.query(
                    `INSERT INTO USER_DISEASES (user_id, disease_id) VALUES ${placeholders}`,
                    values
                );
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

    // ============================================
    // 특수 상태 관련 CRUD
    // ============================================

    // 모든 특수 상태 목록 조회
    static async getAllSpecialConditions() {
        const connection = await dbpool.getConnection();
        try {
            const rows = await connection.query(
                'SELECT id, name, display_name FROM SPECIAL_CONDITIONS ORDER BY display_name'
            );
            return rows;
        } finally {
            connection.release();
        }
    }

    // 유저 특수 상태 조회
    static async getUserSpecialConditions(userId: number) {
        const connection = await dbpool.getConnection();
        try {
            const rows = await connection.query(
                `SELECT sc.id, sc.name, sc.display_name
                 FROM USER_SPECIAL_CONDITIONS usc
                 JOIN SPECIAL_CONDITIONS sc ON usc.condition_id = sc.id
                 WHERE usc.user_id = ?`,
                [userId]
            );
            return rows;
        } finally {
            connection.release();
        }
    }

    // 유저 특수 상태 업데이트 (일괄)
    static async updateUserSpecialConditions(userId: number, conditionIds: number[]) {
        const connection = await dbpool.getConnection();
        try {
            await connection.beginTransaction();

            // 기존 상태 삭제
            await connection.query(
                'DELETE FROM USER_SPECIAL_CONDITIONS WHERE user_id = ?',
                [userId]
            );

            // 새 상태 추가
            if (conditionIds.length > 0) {
                const placeholders = conditionIds.map(() => '(?, ?)').join(', ');
                const values = conditionIds.flatMap(conditionId => [userId, conditionId]);
                await connection.query(
                    `INSERT INTO USER_SPECIAL_CONDITIONS (user_id, condition_id) VALUES ${placeholders}`,
                    values
                );
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

    // ============================================
    // 유저 프로필 업데이트 (기존 함수 확장)
    // ============================================
    static async updateUserHealthProfile(
        userId: number,
        profileData: {
            height?: number;
            weight?: number;
            age_range?: string;
            gender?: string;
        }
    ) {
        const connection = await dbpool.getConnection();
        try {
            const fields: string[] = [];
            const values: any[] = [];

            if (profileData.height !== undefined) {
                fields.push('height = ?');
                values.push(profileData.height);
            }
            if (profileData.weight !== undefined) {
                fields.push('weight = ?');
                values.push(profileData.weight);
            }
            if (profileData.age_range !== undefined) {
                fields.push('age_range = ?');
                values.push(profileData.age_range);
            }
            if (profileData.gender !== undefined) {
                fields.push('gender = ?');
                values.push(profileData.gender);
            }

            if (fields.length > 0) {
                values.push(userId);
                await connection.query(
                    `UPDATE USERS SET ${fields.join(', ')} WHERE id = ?`,
                    values
                );
            }

            return true;
        } finally {
            connection.release();
        }
    }
}

export default UsersModel;