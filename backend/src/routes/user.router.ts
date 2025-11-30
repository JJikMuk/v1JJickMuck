import { Router } from "express";
import UserController from "../controllers/user.controller";
import { authMiddleware } from "../middlewares/auth.middleware";

const userRouter = Router();

userRouter.get('/profile', authMiddleware, UserController.getProfile);
userRouter.patch('/profile', authMiddleware, UserController.updateProfile);

export default userRouter;