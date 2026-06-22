import { Module } from '@nestjs/common';
import { TypeOrmModule } from '@nestjs/typeorm';
import { Ticket } from '../database/entities/ticket.entity';
import { TicketController } from './controllers/ticket.controller';
import { TicketService } from './services/ticket.service';

@Module({
  imports: [TypeOrmModule.forFeature([Ticket])],
  controllers: [TicketController],
  providers: [TicketService],
})
export class TicketModule {}
