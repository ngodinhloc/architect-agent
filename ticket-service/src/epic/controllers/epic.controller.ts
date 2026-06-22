import { Controller, Post, Get, Body, Param, ParseUUIDPipe } from '@nestjs/common';
import { EpicService } from '../services/epic.service';
import { CreateEpicDto } from '../dto/create-epic.dto';

@Controller('api/epic')
export class EpicController {
  constructor(private readonly epicService: EpicService) {}

  @Post()
  create(@Body() dto: CreateEpicDto) {
    return this.epicService.create(dto);
  }

  @Get(':id')
  findOne(@Param('id', ParseUUIDPipe) id: string) {
    return this.epicService.findOne(id);
  }
}
