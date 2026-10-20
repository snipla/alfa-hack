<?php

namespace App\Filament\Resources\Requests\Tables;

use App\Models\Request;
use Filament\Actions\Action;
use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\ViewAction;
use Filament\Schemas\Components\Icon;
use Filament\Support\Enums\TextSize;
use Filament\Support\Icons\Heroicon;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Table;

class RequestsTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('id')
                    ->label('ID заявки')
                    ->numeric()
                    ->sortable(),
                TextColumn::make('status')
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
                    ->size(TextSize::Large)
                    ->sortable(),
                TextColumn::make('created_at')
                    ->label('Создана')
                    ->dateTime('M d Y H:i')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
                TextColumn::make('updated_at')
                    ->label('Обновлена')
                    ->dateTime('M d Y H:i')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->recordActions([
                ViewAction::make(),
                Action::make('take_on_work')
                    ->icon('heroicon-o-pencil')
                    ->label('Взять в обработку')
                    ->action(function ($record) {
                        $record->status = Request::REQUEST_IN_PROCESS;
                        $record->save();
                    })
                    ->requiresConfirmation()
                    ->modalIcon('heroicon-o-question-mark-circle')
                    ->modalHeading('Рассмотреть заявку') // Заголовок
                    ->modalDescription('Вы уверены, что хотите рассмотреть эту заявку?')
                    ->modalSubmitActionLabel('Да, рассмотреть') // Текст кнопки подтверждения
                    ->color('info'),
                EditAction::make(),
            ])
            ->toolbarActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ]);
    }
}
