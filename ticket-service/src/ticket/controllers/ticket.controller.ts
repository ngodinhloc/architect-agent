import { Controller, Post, Get, Body, Param, ParseUUIDPipe } from '@nestjs/common';
import { TicketService } from '../services/ticket.service';
import { CreateTicketDto } from '../dto/create-ticket.dto';

@Controller('api')
export class TicketController {
  constructor(private readonly ticketService: TicketService) {}

  @Post('ticket')
  create(@Body() dto: CreateTicketDto) {
    return this.ticketService.create(dto);
  }

  @Get('epic/:epicId/tickets')
  findByEpic(@Param('epicId', ParseUUIDPipe) epicId: string) {
    return this.ticketService.findByEpic(epicId);
  }

  @Get('ticket/:id')
  findOne(@Param('id', ParseUUIDPipe) id: string) {
    return this.ticketService.findOne(id);
  }
}
