import { Module } from '@nestjs/common';
import { TicketProxyController } from './controllers/ticket-proxy.controller';

@Module({
  controllers: [TicketProxyController],
})
export class TicketModule {}
