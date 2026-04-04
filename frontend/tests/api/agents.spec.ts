import { test, expect } from '@playwright/test';
import { mockLLMAPI } from '../support/mocks';

test.describe('Agents API', () => {
  test.beforeEach(async ({ page }) => {
    mockLLMAPI(page);
  });

  test('should get agents list and chat', async ({ request }) => {
    const agentsResponse = await request.get('/api/agents');
    expect(agentsResponse.ok()).toBeTruthy();
    const agents = await agentsResponse.json();
    expect(agents.length).toBeGreaterThan(0);
    expect(agents.some(agent => agent.name === 'supervisor')).toBeTruthy();

    // Test chat with supervisor agent
    const chatResponse = await request.post('/api/agents/supervisor/chat', {
      data: {
        message: 'Hello',
        model_config: { provider: 'openai', model: 'gpt-4' }
      }
    });
    expect(chatResponse.ok()).toBeTruthy();
    const chatResult = await chatResponse.json();
    expect(chatResult.response).toBeDefined();
    expect(typeof chatResult.response).toEqual('string');
  });

  test('should get agent skills', async ({ request }) => {
    const skillsResponse = await request.get('/api/agents/supervisor/skills');
    expect(skillsResponse.ok()).toBeTruthy();
    const skills = await skillsResponse.json();
    expect(Array.isArray(skills)).toBeTruthy();
  });
});
