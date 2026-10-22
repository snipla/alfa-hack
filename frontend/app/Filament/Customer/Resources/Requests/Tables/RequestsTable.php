<?php

namespace App\Filament\Customer\Resources\Requests\Tables;

use App\Models\Request;
use Faker\Core\Color;
use Filament\Actions\BulkActionGroup;
use Filament\Actions\DeleteBulkAction;
use Filament\Actions\EditAction;
use Filament\Actions\ViewAction;
use Filament\Support\Enums\TextSize;
use Filament\Tables\Columns\TextColumn;
use Filament\Tables\Table;
use Illuminate\Support\Facades\Auth;
use Illuminate\Database\Eloquent\Builder;

class RequestsTable
{
    public static function configure(Table $table): Table
    {
        return $table
            ->modifyQueryUsing(fn(Builder $query) => $query->where('user_id', Auth::id()))
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
            ->filters([
                //
            ])
            ->recordActions([
                ViewAction::make(),
            ])
            ->toolbarActions([
            ]);
    }
}
