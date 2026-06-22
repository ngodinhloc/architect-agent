import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Epic } from '../database/entities/epic.entity';
import { EpicController } from './controllers/epic.controller';
import { EpicService } from './services/epic.service';

@Module({
  imports: [TypeOrmModule.forFeature([Epic])],
  controllers: [EpicController],
  providers: [EpicService],
})
export class EpicModule {}
