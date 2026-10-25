<?php

namespace App\Filament\Customer\Resources\Requests\Schemas;

use App\Models\Request;
use Filament\Actions\Action;
use Filament\Infolists\Components\TextEntry;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;
use Filament\Support\Colors\Color;
use Filament\Support\Enums\TextSize;

class RequestInfolist
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Section::make('Входные данные')
                    ->schema([
                        TextEntry::make('target')
                            ->label('Цель кредитования')
                            ->formatStateUsing(fn($record) => match ($record->target) {
                                'increasing_working_capital' => 'Пополнения оборотных средств',
                                'acquisition_equipment. ' => 'Приобретение оборудования',
                                'commercial_real_estate. ' => 'Коммерческая недвижимость',
                            }),
                        TextEntry::make('borrower')
                            ->label('Кредитор'),
                        TextEntry::make('created_at')
                            ->label('Создана')
                            ->dateTime()
                            ->placeholder('-'),
                        TextEntry::make('updated_at')
                            ->label('Обновлена')
                            ->dateTime()
                            ->placeholder('-'),
                    ]),
                Section::make('Вердикт и комментарий')
                    ->schema([
                        TextEntry::make('status')
                            ->label('Статус заявки')
                            ->badge()
                            ->color(fn($record): string => match ($record->status) {
                                Request::REQUEST_CREATED => 'secondary',
                                Request::REQUEST_IN_PROCESS => 'info',
                                Request::REQUEST_ACCEPTED => 'success',
                                Request::REQUEST_REJECTED => 'danger',
                                Request::CONTRACT_SIGNED => 'secondary',
                                default => 'primary',
                            })
                            ->formatStateUsing(fn($record): string => match ($record->status) {
                                Request::REQUEST_CREATED => 'Создана',
                                Request::REQUEST_IN_PROCESS => 'На рассмотрении',
                                Request::REQUEST_ACCEPTED => 'Одобрена',
                                Request::REQUEST_REJECTED => 'Отклонена',
                                Request::CONTRACT_SIGNED => 'Договор подписан',
                                default => 'primary',
                            })
                            ->size(TextSize::Large),
                        TextEntry::make('admin_comment')
                            ->label('Комментарий администратора')
                            ->placeholder('Заявка ещё не рассмотрена'),

                        Action::make('sign_contract')
                            ->visible(fn($record) => $record->status == Request::REQUEST_ACCEPTED)
                            ->action(function ($record) {
                                $record->status = Request::CONTRACT_SIGNED;
                                $record->save();
//                                dd("Договор подписан!");
                            })
                            ->label('Подписать договор')
                            ->color(Color::Green)
                    ])
            ]);
    }
}
