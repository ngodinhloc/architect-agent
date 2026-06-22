import { Module } from '@nestjs/common';
import { DatabaseModule } from './database/database.module';
import { RedisModule } from './redis/redis.module';
import { RabbitMQModule } from './rabbitmq/rabbitmq.module';
import { ChatModule } from './chat/chat.module';
import { HealthModule } from './health/health.module';
import { TicketModule } from './ticket/ticket.module';

@Module({
  imports: [DatabaseModule, RedisModule, RabbitMQModule, ChatModule, HealthModule, TicketModule],
})
export class AppModule {}
