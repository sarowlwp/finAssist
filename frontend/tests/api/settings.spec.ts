import { test, expect } from '@playwright/test';
import { mockLLMAPI } from '../support/mocks';

test.describe('Settings API', () => {
  test.beforeEach(async ({ page }) => {
    mockLLMAPI(page);
  });

  test('should get and update settings', async ({ request }) => {
    const getResponse = await request.get('/api/settings');
    expect(getResponse.ok()).toBeTruthy();
    const settings = await getResponse.json();
    expect(settings.investment_style).toEqual('balanced');
    expect(settings.model_config).toEqual(
      expect.objectContaining({
        provider: 'openai',
        model: 'gpt-4',
        temperature: 0.7,
        max_tokens: 2000
      })
    );

    // Update investment style
    const styleResponse = await request.put('/api/settings/investment-style', {
      data: { investment_style: 'conservative' }
    });
    expect(styleResponse.ok()).toBeTruthy();
    const updatedStyle = await styleResponse.json();
    expect(updatedStyle.success).toEqual(true);

    // Update model config
    const configResponse = await request.put('/api/settings/model-config', {
      data: {
        provider: 'openrouter',
        model: 'anthropic/claude-3.5-sonnet',
        temperature: 0.5,
        max_tokens: 3000
      }
    });
    expect(configResponse.ok()).toBeTruthy();
    const updatedConfig = await configResponse.json();
    expect(updatedConfig.success).toEqual(true);
  });

  test('should get providers and validate', async ({ request }) => {
    // Mock providers endpoint
    await mockLLMAPI.mockProviders?.(request);

    const providersResponse = await request.get('/api/settings/providers');
    expect(providersResponse.ok()).toBeTruthy();
    const providers = await providersResponse.json();
    expect(Array.isArray(providers)).toBeTruthy();

    // Test provider validation for known providers
    const knownProviders = ['openai', 'openrouter'];
    for (const provider of knownProviders) {
      const validateResponse = await request.get(
        `/api/settings/providers/${provider}/validate`
      );
      expect(validateResponse.ok()).toBeTruthy();
    }
  });
});
