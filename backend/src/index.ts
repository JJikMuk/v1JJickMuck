import express from 'express';
import dotenv from 'dotenv';
import cors from 'cors';
import authRouter from './routes/auth.router';
import userRouter from './routes/user.router';
import imageRouter from './routes/image.router';
import allergyRouter from './routes/allergy.router';
import dashboardRouter from './routes/dashboard.router';

const app = express();
const PORT = process.env.PORT;

app.use(express.json());
app.use(cors())

app.use('/api/auth', authRouter);
app.use('/api/users', userRouter);
app.use('/api/images', imageRouter);
app.use('/api/allergies', allergyRouter);
app.use('/api/dashboard', dashboardRouter);

const startServer = async () => {
  try {
    app.listen(PORT, () => {
      console.log(`🚀 Server is running on http://localhost:${PORT}`);
    });
  } catch (error) {
    console.error('Failed to start server:', error);
    process.exit(1);
  }
};

startServer();