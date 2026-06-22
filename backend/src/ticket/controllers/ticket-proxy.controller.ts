import { Controller, Get, Param, NotFoundException, InternalServerErrorException } from '@nestjs/common';

const TICKET_SERVICE_URL = process.env.TICKET_SERVICE_URL ?? 'http://localhost:8003';

async function proxyGet(url: string, notFoundMsg?: string) {
  const res = await fetch(url);
  if (res.status === 404) throw new NotFoundException(notFoundMsg ?? 'Not found');
  if (!res.ok) throw new InternalServerErrorException('Ticket service error');
  return res.json();
}

@Controller('api')
export class TicketProxyController {
  @Get('epic/:id')
  getEpic(@Param('id') id: string) {
    return proxyGet(`${TICKET_SERVICE_URL}/api/epic/${id}`, `Epic ${id} not found`);
  }

  @Get('epic/:epicId/tickets')
  getEpicTickets(@Param('epicId') epicId: string) {
    return proxyGet(`${TICKET_SERVICE_URL}/api/epic/${epicId}/tickets`);
  }

  @Get('ticket/:id')
  getTicket(@Param('id') id: string) {
    return proxyGet(`${TICKET_SERVICE_URL}/api/ticket/${id}`, `Ticket ${id} not found`);
  }
}
