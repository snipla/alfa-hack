<?php

namespace App\Filament\Customer\Widgets;

use Filament\Widgets\Widget;

class CreditOfferWidget extends Widget
{
    protected string $view = 'filament.customer.widgets.credit-offer-widget';
    protected int|string|array $columnSpan = 'full';

    protected static ?int $sort = 1;

    protected function getViewData(): array
    {
        return [
            'offers' => [
                [
                    'title' => 'Потребительский кредит',
                    'bank' => 'Альфа-Банк',
                    'description' => 'Без залога и поручителей. Решение за 2 минуты.',
                    'rate' => 12.9,
                    'amount' => 5_000_000,
                    'term' => 60,
                    'badge' => null,
                    'badge_color' => 'success',
                    'icon' => 'heroicon-o-fire',
                ],
                [
                    'title' => 'Кредит наличными «Проще»',
                    'bank' => 'Альфа-Банк',
                    'description' => 'Деньги на карту в день обращения. Без справок.',
                    'rate' => 14.5,
                    'amount' => 3_000_000,
                    'term' => 36,
                    'badge' => null,
                    'badge_color' => 'warning',
                    'icon' => 'heroicon-o-bolt',
                ],
                [
                    'title' => 'Рефинансирование',
                    'bank' => 'Альфа-Банк',
                    'description' => 'Объедините до 5 кредитов в один.',
                    'rate' => 9.8,
                    'amount' => 10_000_000,
                    'term' => 84,
                    'badge' => null,
                    'badge_color' => 'info',
                    'icon' => 'heroicon-o-arrow-path-rounded-square',
                ],
                [
                    'title' => 'Кредит под залог авто',
                    'bank' => 'Альфа-Банк',
                    'description' => 'Автомобиль остаётся у вас. Ставка ниже на 5%.',
                    'rate' => 11.2,
                    'amount' => 7_500_000,
                    'term' => 60,
                    'badge' => null,
                    'badge_color' => null,
                    'icon' => 'heroicon-o-truck',
                ],
                [
                    'title' => 'Кредит для ИП',
                    'bank' => 'Альфа-Банк',
                    'description' => 'Без залога и поручителей. Упрощённое одобрение.',
                    'rate' => 15.9,
                    'amount' => 1000000,
                    'term' => 48,
                    'badge' => null,
                    'badge_color' => 'primary',
                    'icon' => 'heroicon-o-briefcase',
                ],
                [
                    'title' => 'Кредитная карта «120 дней»',
                    'bank' => 'Альфа-Банк',
                    'description' => 'Беспроцентный период 120 дней. Кэшбэк до 5%.',
                    'rate' => 0,
                    'amount' => 1_000_000,
                    'term' => null,
                    'badge' => null,
                    'badge_color' => 'success',
                    'icon' => 'heroicon-o-credit-card',
                ],
            ],
        ];
    }

}
