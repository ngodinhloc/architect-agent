import { Entity, Column, PrimaryColumn, CreateDateColumn } from 'typeorm';

@Entity('tickets')
export class Ticket {
  @PrimaryColumn({ type: 'uuid' })
  id!: string;

  @Column({ type: 'uuid' })
  epicId!: string;

  @Column({ type: 'varchar', length: 500 })
  name!: string;

  @Column({ type: 'jsonb', default: '[]' })
  requirements!: Record<string, unknown>[];

  @Column({ type: 'jsonb', default: '[]' })
  acceptance_criteria!: Record<string, unknown>[];

  @CreateDateColumn()
  createdAt!: Date;
}
