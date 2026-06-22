import { Module } from '@nestjs/common';
import { DatabaseModule } from './database/database.module';
import { EpicModule } from './epic/epic.module';
import { TicketModule } from './ticket/ticket.module';
import { HealthModule } from './health/health.module';

@Module({
  imports: [DatabaseModule, EpicModule, TicketModule, HealthModule],
})
export class AppModule {}
