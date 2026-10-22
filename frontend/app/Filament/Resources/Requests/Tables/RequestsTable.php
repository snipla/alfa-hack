<?php

namespace App\Filament\Resources\Requests\Tables;

use App\Filament\Resources\Requests\Pages\ManageRequests;
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
use Filament\Tables\Filters\SelectFilter;
use Filament\Tables\Table;
use Illuminate\Contracts\Support\Htmlable;

class RequestsTable
{
    protected static ?string $breadcrumb = 'Все пользователи';

    public static function configure(Table $table): Table
    {
        return $table
            ->columns([
                TextColumn::make('id')
                    ->label('ID заявки')
                    ->numeric()
                    ->sortable(),
                TextColumn::make('user.name')
                    ->label('Имя пользователя')
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
                    ->size(TextSize::Large)
                    ->sortable(),
                TextColumn::make('created_at')
                    ->label('Создана')
                    ->dateTime('M d Y H:i')
                    ->sortable()
                    ->toggleable(isToggledHiddenByDefault: true),
//                TextColumn::make('updated_at')
//                    ->label('Обновлена')
//                    ->dateTime('M d Y H:i')
//                    ->sortable()
//                    ->toggleable(isToggledHiddenByDefault: true),
            ])
            ->recordActions([
                ViewAction::make(),
                Action::make('take_on_work')
                    ->icon('heroicon-o-pencil')
                    ->label(fn($record): string => match ($record->status) {
                        Request::REQUEST_CREATED => 'Взять на рассмотрение',
                        Request::REQUEST_IN_PROCESS => 'Продолжить рассмотрение',
                    })
                    ->visible(fn($record) => $record->status == Request::REQUEST_CREATED || $record->status ==
                        Request::REQUEST_IN_PROCESS)
                    ->action(function ($record) {
                        $record->status = Request::REQUEST_IN_PROCESS;
                        $record->save();
                        redirect(ManageRequests::getUrl(['record' => $record->id]));
                    })
                    ->requiresConfirmation()
                    ->modalIcon('heroicon-o-question-mark-circle')
                    ->modalHeading('Рассмотреть заявку') // Заголовок
                    ->modalDescription('Вы уверены, что хотите рассмотреть эту заявку?')
                    ->modalSubmitActionLabel('Да, рассмотреть') // Текст кнопки подтверждения
                    ->color('info'),
                EditAction::make(),
            ])
            ->filters([
                SelectFilter::make('status')
                    ->label('Статус')
                    ->options([
                        Request::REQUEST_CREATED => 'Создана',
                        Request::REQUEST_IN_PROCESS => 'На рассмотрении',
                        Request::REQUEST_ACCEPTED => 'Одобрена',
                        Request::REQUEST_REJECTED => 'Отклонена',
                        Request::CONTRACT_SIGNED => 'Договор подписан',
                    ])
            ])
            ->toolbarActions([
                BulkActionGroup::make([
                    DeleteBulkAction::make(),
                ]),
            ]);
    }
}
