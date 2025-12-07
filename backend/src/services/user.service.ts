import UsersModel from '../models/user.model';

class UserService {
    // ============================================
    // 유저 전체 프로필 (RAG API용)
    // ============================================
    static async getUserFullProfile(userUuid: string) {
        return await UsersModel.getUserFullProfile(userUuid);
    }

    static async getUserIdByUuid(userUuid: string) {
        return await UsersModel.getUserIdByUuid(userUuid);
    }

    static async getUserWithAllergies(userId: number) {
        return await UsersModel.getUserWithAllergies(userId);
    }

    static async updateUserProfile(userId: number, name?: string, dietType?: string | null, allergyIds?: number[]) {
        return await UsersModel.updateUserProfile(userId, name, dietType, allergyIds);
    }

    // ============================================
    // 질병 관련
    // ============================================
    static async getAllDiseases() {
        return await UsersModel.getAllDiseases();
    }

    static async getUserDiseases(userId: number) {
        return await UsersModel.getUserDiseases(userId);
    }

    static async updateUserDiseases(userId: number, diseaseIds: number[]) {
        return await UsersModel.updateUserDiseases(userId, diseaseIds);
    }

    // ============================================
    // 특수 상태 관련
    // ============================================
    static async getAllSpecialConditions() {
        return await UsersModel.getAllSpecialConditions();
    }

    static async getUserSpecialConditions(userId: number) {
        return await UsersModel.getUserSpecialConditions(userId);
    }

    static async updateUserSpecialConditions(userId: number, conditionIds: number[]) {
        return await UsersModel.updateUserSpecialConditions(userId, conditionIds);
    }

    // ============================================
    // 건강 프로필 업데이트
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
        return await UsersModel.updateUserHealthProfile(userId, profileData);
    }
}

export default UserService;