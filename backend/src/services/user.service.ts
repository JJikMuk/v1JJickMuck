import UserModel from "../models/user.model";

class UserService {
    static async getUserByUUID(uuid: string) {
        // 1. UUID로 user_id 가져오기
        const userId = await UserModel.getUserIdByUuid(uuid);

        if (!userId) {
            return null;
        }

        // 2. user_id로 유저 정보 + 알레르기 정보 가져오기
        const userWithAllergies = await UserModel.getUserWithAllergies(userId);

        return userWithAllergies;
    }

    static async updateUserProfile(uuid: string, name?: string, dietType?: string | null, allergyIds?: number[]) {
        // 1. UUID로 user_id 가져오기
        const userId = await UserModel.getUserIdByUuid(uuid);

        if (!userId) {
            throw new Error("User not found");
        }

        // 2. 프로필 업데이트
        await UserModel.updateUserProfile(userId, name, dietType, allergyIds);

        // 3. 업데이트된 유저 정보 반환
        const updatedUser = await UserModel.getUserWithAllergies(userId);

        return updatedUser;
    }
}

export default UserService;