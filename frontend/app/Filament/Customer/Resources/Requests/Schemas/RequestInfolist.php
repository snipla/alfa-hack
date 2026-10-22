<?php

namespace App\Filament\Customer\Resources\Requests\Schemas;

use App\Models\Request;
use Filament\Infolists\Components\TextEntry;
use Filament\Schemas\Components\Section;
use Filament\Schemas\Schema;
use Filament\Support\Enums\TextSize;

class RequestInfolist
{
    public static function configure(Schema $schema): Schema
    {
        return $schema
            ->components([
                Section::make('Входные данные')
                    ->schema([
                        TextEntry::make('user_id')
                            ->numeric(),
                        TextEntry::make('credit_info')
                            ->placeholder('-')
                            ->columnSpanFull(),
                        TextEntry::make('created_at')
                            ->dateTime()
                            ->placeholder('-'),
                        TextEntry::make('updated_at')
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
                                default => 'primary',
                            })
                            ->formatStateUsing(fn($record): string => match ($record->status) {
                                Request::REQUEST_CREATED => 'Создана',
                                Request::REQUEST_IN_PROCESS => 'На рассмотрении',
                                Request::REQUEST_ACCEPTED => 'Одобрена',
                                Request::REQUEST_REJECTED => 'Отклонена',
                                default => 'primary',
                            })
                            ->size(TextSize::Large),
                        TextEntry::make('admin_comment')
                            ->label('Комментарий администратора')
                            ->placeholder('Заявка ещё не рассмотрена'),
                    ])
            ]);
    }
}
