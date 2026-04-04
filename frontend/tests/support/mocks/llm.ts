import { Page } from '@playwright/test';

export function mockLLMAPI(page: Page) {
  page.route('**/api/agents/*/chat', async (route) => {
    const url = route.request().url();
    const agentName = url.split('/').pop();
    await route.fulfill({
      status: 200,
      json: {
        response: `This is a mock response from the ${agentName} agent`
      }
    });
  });

  page.route('**/api/analysis/*', async (route) => {
    await route.fulfill({
      status: 200,
      json: {
        task_id: 'test-task-123',
        status: 'completed',
        results: [
          {
            agent: 'news',
            analysis: 'News analysis: Positive sentiment'
          },
          {
            agent: 'fundamentals',
            analysis: 'Fundamentals: Strong financial position'
          }
        ]
      }
    });
  });

  page.route('**/api/portfolio**', async (route) => {
    const method = route.request().method();
    const url = route.request().url();

    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        json: []
      });
    } else if (method === 'POST') {
      const requestBody = route.request().postDataJSON();
      await route.fulfill({
        status: 201,
        json: {
          ticker: requestBody.ticker,
          quantity: requestBody.quantity,
          cost_price: requestBody.cost_price,
          note: requestBody.note,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      });
    } else if (method === 'PUT') {
      const requestBody = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        json: {
          ticker: url.split('/').pop(),
          quantity: requestBody.quantity || 100,
          cost_price: requestBody.cost_price || 150,
          note: requestBody.note,
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString()
        }
      });
    } else if (method === 'DELETE') {
      await route.fulfill({
        status: 204
      });
    }
  });

  page.route('**/api/settings', async (route) => {
    const method = route.request().method();

    if (method === 'GET') {
      await route.fulfill({
        status: 200,
        json: {
          investment_style: 'balanced',
          llm_config: {
            provider: 'openrouter',
            model: 'anthropic/claude-3.5-sonnet',
            temperature: 0.7,
            max_tokens: 2000
          },
          agent_model_configs: {},
          agent_skills: {},
          custom_agents: {},
          updated_at: new Date().toISOString()
        }
      });
    } else if (method === 'PUT') {
      const requestBody = route.request().postDataJSON();
      await route.fulfill({
        status: 200,
        json: {
          investment_style: requestBody.investment_style || 'balanced',
          llm_config: {
            provider: 'openrouter',
            model: 'anthropic/claude-3.5-sonnet',
            temperature: 0.7,
            max_tokens: 2000
          },
          agent_model_configs: {},
          agent_skills: {},
          custom_agents: {},
          updated_at: new Date().toISOString()
        }
      });
    }
  });
}
