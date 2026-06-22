import { Entity, Column, PrimaryColumn, CreateDateColumn } from 'typeorm';

@Entity('epics')
export class Epic {
  @PrimaryColumn({ type: 'uuid' })
  id!: string;

  @Column({ type: 'varchar', length: 500 })
  name!: string;

  @Column({ type: 'jsonb', default: '[]' })
  requirements!: Record<string, unknown>[];

  @Column({ type: 'jsonb' })
  solution!: Record<string, unknown>;

  @CreateDateColumn()
  createdAt!: Date;
}
