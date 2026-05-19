import { describe, it, expect } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/vue'
import HomeView from '../HomeView.vue'

describe('HomeView', () => {
  it('renders welcome message', () => {
    render(HomeView)
    expect(screen.getByTestId('welcome-message').textContent).toBe('Welcome to the platform')
  })

  it('shows initial count as 0', () => {
    render(HomeView)
    expect(screen.getByTestId('increment-btn').textContent).toContain('Count: 0')
  })

  it('increments count when button is clicked', async () => {
    render(HomeView)
    const button = screen.getByTestId('increment-btn')
    await fireEvent.click(button)
    expect(button.textContent).toContain('Count: 1')
  })
})
