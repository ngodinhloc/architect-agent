import { Injectable, NestMiddleware } from '@nestjs/common';
import { Request, Response, NextFunction } from 'express';
import { decodeJwt } from 'jose';
import { AppLogger } from '../../common/logger/app-logger';

const SKIP_PATHS = new Set(['/api/health', '/api/.well-known/jwks', '/metrics']);

export interface AuthUser {
  username: string;
  email: string;
  name: string;
}

declare global {
  // eslint-disable-next-line @typescript-eslint/no-namespace
  namespace Express {
    interface Request {
      user?: AuthUser;
    }
  }
}

@Injectable()
export class KeycloakAuthMiddleware implements NestMiddleware {
  private readonly logger = new AppLogger();

  async use(req: Request, res: Response, next: NextFunction) {
    const path = req.originalUrl.split('?')[0];
    if (SKIP_PATHS.has(path)) {
      return next();
    }

    const token = this.extractToken(req);
    if (!token) {
      this.logger.warn('KeycloakAuthMiddleware: Missing kc_token cookie', { path });
      return res.status(401).json({ message: 'Unauthorized' });
    }

    try {
      // Kong already verified the signature — just decode to extract user claims
      const payload = decodeJwt(token);
      req.user = {
        username: (payload['preferred_username'] as string) ?? '',
        email: (payload['email'] as string) ?? '',
        name: (payload['name'] as string) ?? (payload['preferred_username'] as string) ?? '',
      };
      this.logger.log('KeycloakAuthMiddleware: user resolved', {
        username: req.user.username,
        path,
      });
      return next();
    } catch (err) {
      this.logger.warn('KeycloakAuthMiddleware: failed to decode token', {
        path,
        error: (err as Error).message,
      });
      return res.status(401).json({ message: 'Unauthorized' });
    }
  }

  private extractToken(req: Request): string | null {
    const cookieHeader = req.headers['cookie'] ?? '';
    const match = /(?:^|;\s*)kc_token=([^;]+)/.exec(cookieHeader);
    return match ? decodeURIComponent(match[1]) : null;
  }
}
